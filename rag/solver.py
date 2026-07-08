"""
solver.py
---------
Reference-augmented step-by-step solver for numerical / problem-solving
questions.

Unlike generate_answer() (which is strictly constrained to retrieved context),
this solver treats the retrieved textbook chunks as *reference material* —
relevant formulas, definitions, and unit relationships — and then applies
full mathematical / scientific reasoning to produce a worked solution.

This means:
- If RAG retrieves a relevant formula → the solver uses it as the authoritative
  source and cites it naturally ("Using the formula from the textbook…").
- If RAG retrieves nothing → the solver still produces a complete solution
  from its own knowledge (no hard failure).
- Either way, every solution follows the structured format:
  Given → Formula → Steps → Final Answer.
"""

from __future__ import annotations

import logging
import os
import time

from openai import APIConnectionError, APIStatusError, OpenAI
from dotenv import load_dotenv

from config import MODEL_NAME, OPENROUTER_BASE_URL, OPENROUTER_SITE_URL, OPENROUTER_SITE_NAME

load_dotenv()

log = logging.getLogger(__name__)

# ── Re-use the same OpenRouter client pattern as generator.py ─────────────────
_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=OPENROUTER_BASE_URL,
    default_headers={
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_SITE_NAME,
    },
)

# ── System prompts ────────────────────────────────────────────────────────────

_BASE_SOLVER_PROMPT = """
You are Edhanta Tutor, an expert board-level tutor skilled in Mathematics,
Physics, and Chemistry.

Your task is to solve a numerical / problem-solving question step-by-step.

You will be given:
1. (Optional) Relevant textbook excerpts containing formulas and theory.
2. The question to solve.

Rules:
- If textbook excerpts are provided, use the formulas and definitions from
  them as your primary reference. Refer to them naturally (e.g. "Using the
  formula given in the textbook…"). Do NOT ignore them.
- If no textbook excerpts are provided, solve using your own knowledge.
- Always structure your answer as:
    **Given:** (list all known values with units)
    **Formula:** (state the formula used, in LaTeX)
    **Solution:** (show every step clearly)
    **Answer:** (highlight the final result, boxed or bolded)
- For MCQs: ALWAYS begin your response with this exact block BEFORE any explanation:

  > ✅ **Correct Answer: (X) [option text]**
  >
  > | Option | Text |
  > |--------|------|
  > | (A)    | ...  |
  > | (B)    | ...  |
  > | (C)    | ...  |
  > | (D)    | ...  |

  Then, after the block, explain WHY that option is correct and why the others are wrong.
  Never bury the answer inside the explanation — it must appear at the very top.

- Calibrate depth to the marks available:
    1 mark → brief direct answer
    2–3 marks → key steps shown
    4–5 marks → full detailed working
- Never skip steps. A student should be able to follow every line.
- Do NOT add unnecessary commentary or repeat the question.

Mathematical Formatting (IMPORTANT):
- Use LaTeX for all math expressions.
- Inline math: \\( ... \\)   e.g. \\( F = ma \\)
- Display equations: \\[ ... \\]  e.g. \\[ v^2 = u^2 + 2as \\]
- Use \\frac{}{}, \\sqrt{}, \\times, \\cdot, ^{}, _{}, \\alpha, \\beta etc.
""".strip()

_CBSE_ADDENDUM = """
Format rules (CBSE board):
- Use point-wise / step-numbered format.
- Highlight key terms in **bold**.
- Be concise but complete.
"""

_MH_ADDENDUM = """
Format rules (Maharashtra board):
- Follow: Definition → Formula → Solved Steps → Conclusion.
- Use clear numbered steps.
"""

_MAX_CONTEXT_CHARS = 3000  # slightly larger than generator.py — formulas are dense


def solve_with_context(
    question: str,
    context: str,
    marks: str,
    subject: str,
    board: str,
    history: list,
) -> str:
    """Solve *question* using retrieved *context* as reference material.

    Args:
        question: The extracted question text.
        context:  Newline-joined RAG chunks (may be empty string).
        marks:    Mark allocation hint, e.g. ``"3"`` or ``"5"`` (may be ``""``).
        subject:  Subject string from vision extractor, e.g. ``"Physics"``.
        board:    ``"CBSE"`` or ``"MH"``.
        history:  Conversation history list (same format as memory.py).

    Returns:
        Solved answer string (may contain LaTeX).
    """
    # ── Build system prompt ───────────────────────────────────────────────────
    system = _BASE_SOLVER_PROMPT
    system += _CBSE_ADDENDUM if board == "CBSE" else _MH_ADDENDUM

    if marks:
        system += f"\n\nThis question carries **{marks} mark(s)**. Calibrate depth accordingly."

    if subject:
        system += f"\n\nSubject context: {subject}."

    # ── Build messages ────────────────────────────────────────────────────────
    messages: list[dict] = [{"role": "system", "content": system}]

    # Inject sliding-window conversation history
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})

    # ── Compose the user turn ─────────────────────────────────────────────────
    if context:
        if len(context) > _MAX_CONTEXT_CHARS:
            context = context[:_MAX_CONTEXT_CHARS] + "\n[... context trimmed ...]"

        user_content = (
            "[TEXTBOOK REFERENCE START]\n"
            f"{context}\n"
            "[TEXTBOOK REFERENCE END]\n\n"
            "The textbook excerpts above contain relevant formulas and theory. "
            "Use them as your primary reference.\n\n"
            f"Now solve this question:\n{question}"
        )
    else:
        # No RAG context — solve from own knowledge
        user_content = (
            "No textbook context was retrieved for this question.\n"
            "Solve the following question step-by-step using your knowledge:\n\n"
            f"{question}"
        )

    messages.append({"role": "user", "content": user_content})

    # ── Call OpenRouter with retries ──────────────────────────────────────────
    for attempt in range(3):
        try:
            log.info(
                "[SOLVER] OpenRouter call (model=%s, attempt=%d, context_len=%d)",
                MODEL_NAME, attempt + 1, len(context),
            )
            response = _client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,  # type: ignore[arg-type]
            )
            answer = (response.choices[0].message.content or "").strip()
            if not answer:
                raise ValueError("Solver received an empty response from the model.")
            log.info("[SOLVER] Answer generated (%d chars)", len(answer))
            return answer

        except APIStatusError as exc:
            if exc.status_code >= 500 and attempt < 2:
                log.warning("[SOLVER] OpenRouter 5xx (%d), retrying…", exc.status_code)
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError(
                    f"[SOLVER] OpenRouter error {exc.status_code}: {exc.message}"
                ) from exc

        except APIConnectionError as exc:
            if attempt < 2:
                log.warning("[SOLVER] Connection error, retrying…")
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError(
                    "[SOLVER] Could not reach OpenRouter after 3 attempts."
                ) from exc

    raise RuntimeError("[SOLVER] solve_with_context: exhausted all retries.")
