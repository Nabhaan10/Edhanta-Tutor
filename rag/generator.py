import os
import time
import logging
from openai import OpenAI, APIStatusError, APIConnectionError
from dotenv import load_dotenv

from config import MODEL_NAME, OPENROUTER_BASE_URL, OPENROUTER_SITE_URL, OPENROUTER_SITE_NAME

log = logging.getLogger(__name__)

load_dotenv()

# ── OpenRouter client (OpenAI-compatible) ─────────────────────────────────────
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=OPENROUTER_BASE_URL,
    default_headers={
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_SITE_NAME,
    },
)

# ── System prompts ────────────────────────────────────────────────────────────

BASE_SYSTEM_INSTRUCTION = """
You are Edhanta Tutor, a friendly and expert board tutor.
You MUST answer ONLY using the retrieved context.

If the retrieved context does not contain enough information to answer the question, reply exactly:

"I couldn't find this topic in the available textbooks."

Do NOT use your own knowledge.
Do NOT guess.
Do NOT answer from memory.
Rules:
- Start with the direct answer, then explain further.
- Use simple language; avoid jargon.
- Don't quote the context verbatim — teach naturally.
- Don't say "According to the context..." or similar phrases.
- For "What is" → define first. "Explain" → structured. "Difference" → table/bullets. "Why/How" → step-by-step. "X marks" → match length.
- Only ask a follow-up question if it genuinely helps learning. Don't end every reply with a question.

- If the question is numerical or involves calculations:
- Start with "Given".
- List all known values.
- Mention the formula used.
- Show every calculation step.
- Highlight the final answer clearly.
- For MCQs: ALWAYS begin your response with this exact block BEFORE any explanation:

  > ✅ **Correct Answer: (X) [option text]**
  >
  > | Option | Text |
  > |--------|------|
  > | (A)    | ...  |
  > | (B)    | ...  |
  > | (C)    | ...  |
  > | (D)    | ...  |

  Then explain WHY that option is correct and why the others are wrong.
  Never bury the answer inside the explanation — it must appear at the very top.

- Never skip mathematical steps.

Mathematical Formatting (IMPORTANT):
- Always write mathematical expressions using LaTeX notation.
- Inline math (within a sentence): use \( ... \) delimiters. Example: The formula is \( E = mc^2 \).
- Display equations (on their own line): use \[ ... \] delimiters. Example:
  \[
  \cos^2 A + \sin^2 A = 1
  \]
- Use proper LaTeX for: fractions (\frac{a}{b}), powers (x^{2}), subscripts (x_{i}), Greek letters (\alpha, \beta, \theta), roots (\sqrt{x}), sums (\sum), integrals (\int), etc.
- Never write raw math without LaTeX (e.g., write \( x^2 + y^2 \) not x^2 + y^2).
""".strip()

CBSE_RULES = """
Answer in:
- Point-wise format
- Exam-oriented
- Concise
- Highlight keywords
"""

MS_RULES = """
Answer in:
- Definition
- Explanation
- Important Points
- Conclusion
"""

_MAX_CONTEXT_CHARS = 2000


def generate_answer(question: str, context: str, history: list, board: str) -> str:
    # Truncate context to avoid inflating the prompt
    if len(context) > _MAX_CONTEXT_CHARS:
        context = context[:_MAX_CONTEXT_CHARS] + "..."

    # Build system instruction based on board
    system_instruction = BASE_SYSTEM_INSTRUCTION
    system_instruction += CBSE_RULES if board == "CBSE" else MS_RULES

    # Build messages list (OpenAI chat format)
    messages = [{"role": "system", "content": system_instruction}]

    # Inject sliding-window history
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})

    # Final user turn: labelled context block + question
    user_content = (
        f"[TEXTBOOK CONTEXT START]\n{context}\n[TEXTBOOK CONTEXT END]\n\n"
        f"Using ONLY the textbook context above, answer this question:\n{question}"
    )
    messages.append({"role": "user", "content": user_content})

    for attempt in range(3):
        try:
            log.info("OpenRouter API called (model=%s, attempt=%d)", MODEL_NAME, attempt + 1)
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
            )
            answer = (response.choices[0].message.content or "").strip()
            if not answer:
                raise ValueError("Empty response from model.")
            return answer

        except APIStatusError as e:
            # 5xx → retry with backoff; 4xx → fail fast
            if e.status_code >= 500 and attempt < 2:
                log.warning("OpenRouter server error %d, retrying…", e.status_code)
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError(f"OpenRouter error {e.status_code}: {e.message}") from e

        except APIConnectionError as e:
            if attempt < 2:
                log.warning("OpenRouter connection error, retrying…")
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError("Could not reach OpenRouter after 3 attempts.") from e

    raise RuntimeError("generate_answer: exhausted all retries.")