"""
vision_extractor.py
-------------------
Phase 4 — Question Image Solver.

Sends an uploaded image to the OpenRouter multimodal endpoint and extracts
the academic question (plus optional metadata) as structured JSON.

This is the *only* new component in the RAG pipeline.  The returned
``question`` field is fed directly into the existing ``ask()`` function in
``rag/chatbot.py`` — no other pipeline files are modified.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import TypedDict

from openai import APIConnectionError, APIStatusError, OpenAI
from dotenv import load_dotenv

from config import OPENROUTER_BASE_URL, OPENROUTER_SITE_NAME, OPENROUTER_SITE_URL, MODEL_NAME

load_dotenv()

log = logging.getLogger(__name__)

# ── Re-use the same OpenRouter client settings as generator.py ────────────────
_vision_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=OPENROUTER_BASE_URL,
    default_headers={
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_SITE_NAME,
    },
)

# Supported MIME types → base64 data-URI prefix
_SUPPORTED_MIME = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
}

# ── Extraction prompt ─────────────────────────────────────────────────────────
_EXTRACTION_PROMPT = """\
You are an expert academic question extractor. Your job is to read this image
of an exam question and produce a complete, self-contained question text that
includes EVERY piece of information a student would need to solve it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL — DIAGRAMS AND FIGURES (read this carefully):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the image contains any diagram, figure, shape, graph, or circuit:

1. READ every number, label, unit, and symbol written ON or NEAR the diagram.
   Do NOT skip any value — even small labels in corners or along edges.

2. EMBED all diagram information directly into the "question" field.
   Use natural language like:
   - "In the given triangle ABC, AB = 6 cm, BC = 8 cm, angle B = 90°."
   - "A circuit has a resistor of 4Ω and a battery of 12V connected in series."
   - "The graph shows a velocity-time graph where initial velocity = 20 m/s
     and the line reaches 0 m/s at t = 5 s."
   - "In the figure, O is the centre of the circle, OA = 5 cm, angle AOB = 60°."

3. NEVER say "as shown in the figure" or "from the diagram" without first
   describing what the figure shows and listing all its values.

4. If there are multiple sub-questions (a, b, c...), include ALL of them.

Types of diagram values you MUST extract:
- Triangle/polygon: side lengths, angles, area labels
- Circle: radius, diameter, arc length, chord length, angle at centre
- Coordinate geometry: coordinates of points, slope values
- Physics circuits: resistance (Ω), voltage (V), current (A), capacitance (F)
- Physics motion diagrams: velocity, acceleration, distance, time values
- Chemistry diagrams: temperature, pressure, volume, concentration values
- Bar/line graphs: axis labels, scale values, specific data points
- Number lines: marked values and their positions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MCQ QUESTIONS (Multiple Choice):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the question is a multiple-choice question (has options A, B, C, D or
similar), you MUST include ALL option texts verbatim in the "question" field.

Format options inside the question text like this:
  "Which of the following is correct?\n(A) ...\n(B) ...\n(C) ...\n(D) ..."

Do NOT drop any option. Even if you think one is obviously wrong, include it.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Also extract:
- subject:       e.g. "Mathematics", "Physics", "Chemistry", "Biology"
- topic:         e.g. "Triangles", "Ohm's Law", "Quadratic Equations"
- marks:         numeric value if visible on the paper, e.g. "3", "5"
- question_type: one of: "theory", "numerical", "mcq", "diagram", "proof",
                 "short answer", "long answer"

Return ONLY valid JSON. No explanation, no markdown fences, no extra text.

{
    "question": "Complete self-contained question text with ALL diagram values and MCQ options embedded",
    "subject": "...",
    "topic": "...",
    "marks": "...",
    "question_type": "..."
}

Do NOT answer the question. Do NOT skip any numerical value or MCQ option from the image.\
"""




class ExtractedQuestion(TypedDict):
    question: str
    subject: str
    topic: str
    marks: str
    question_type: str


# ── Public API ────────────────────────────────────────────────────────────────

def extract_question(image_bytes: bytes, mime_type: str) -> ExtractedQuestion:
    """Send *image_bytes* to the vision model and return structured metadata.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        mime_type:   MIME type string, e.g. ``"image/jpeg"`` or ``"image/png"``.

    Returns:
        :class:`ExtractedQuestion` dict with ``question``, ``subject``,
        ``topic``, ``marks``, and ``question_type`` keys.

    Raises:
        ValueError: For unsupported formats, empty images, or no question found.
        RuntimeError: For API errors after retries.
    """
    # ── Validate ──────────────────────────────────────────────────────────────
    if not image_bytes:
        raise ValueError("Uploaded image is empty.")

    normalised_mime = _SUPPORTED_MIME.get(mime_type.lower())
    if not normalised_mime:
        raise ValueError(
            f"Unsupported image format '{mime_type}'. "
            "Please upload a JPEG or PNG image."
        )

    # ── Encode as base64 data URI ─────────────────────────────────────────────
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:{normalised_mime};base64,{b64}"

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": data_uri},
                },
                {
                    "type": "text",
                    "text": _EXTRACTION_PROMPT,
                },
            ],
        }
    ]

    # ── Call OpenRouter with retries ──────────────────────────────────────────
    raw_json: str = ""
    for attempt in range(3):
        try:
            log.info(
                "Vision extraction request (model=%s, attempt=%d, bytes=%d)",
                MODEL_NAME,
                attempt + 1,
                len(image_bytes),
            )
            response = _vision_client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,  # type: ignore[arg-type]
            )
            raw_json = (response.choices[0].message.content or "").strip()
            break

        except APIStatusError as exc:
            if exc.status_code >= 500 and attempt < 2:
                log.warning("OpenRouter 5xx on vision call, retrying… (%d)", exc.status_code)
                time.sleep(2**attempt)
            else:
                raise RuntimeError(
                    f"Vision API error {exc.status_code}: {exc.message}"
                ) from exc

        except APIConnectionError as exc:
            if attempt < 2:
                log.warning("OpenRouter connection error on vision call, retrying…")
                time.sleep(2**attempt)
            else:
                raise RuntimeError(
                    "Could not reach OpenRouter after 3 attempts."
                ) from exc

    if not raw_json:
        raise ValueError("The vision model returned an empty response. The image may be unreadable.")

    # ── Parse JSON ────────────────────────────────────────────────────────────
    # The model sometimes wraps the JSON in markdown fences despite the prompt.
    cleaned = raw_json
    if cleaned.startswith("```"):
        # Strip ```json ... ``` or ``` ... ``` fences
        lines = cleaned.splitlines()
        cleaned = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()

    try:
        data: dict = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        log.error("Vision model returned non-JSON: %s", raw_json[:500])
        raise ValueError(
            "Could not parse the model's response. The image may be unclear or contain no readable text."
        ) from exc

    question = (data.get("question") or "").strip()
    if not question or question in {"...", "null", "N/A", ""}:
        raise ValueError(
            "No academic question could be found in the image. "
            "Please upload a clearer photo of the question."
        )

    return ExtractedQuestion(
        question=question,
        subject=(data.get("subject") or "").strip(),
        topic=(data.get("topic") or "").strip(),
        marks=str(data.get("marks") or "").strip(),
        question_type=(data.get("question_type") or "").strip(),
    )
