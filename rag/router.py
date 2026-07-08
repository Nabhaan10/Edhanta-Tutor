"""
router.py
---------
QuestionRouter — decides the solver strategy for an image question.

Routes are decided from vision-extracted metadata (not from the retrieved
context) so the decision is fast and never requires an extra LLM call.

Supported routes
----------------
"theory"    → generate_answer() — strict context-only RAG generation.
"numerical" → solve_with_context() — reference-augmented step-by-step solver.

The router is intentionally extensible: adding a new route (e.g.
"derivation", "programming", "diagram") only requires adding a new
detection block in _collect_signals() and a new branch in app.py.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rag.vision_extractor import ExtractedQuestion

log = logging.getLogger(__name__)

# ── Signal tables ─────────────────────────────────────────────────────────────

# question_type strings returned by the vision model that strongly indicate
# a numerical / problem-solving question
_NUMERICAL_QUESTION_TYPES: frozenset[str] = frozenset({
    "numerical",
    "calculation",
    "problem",
    "problem solving",
    "problem-solving",
    "mcq",
    "multiple choice",
    "application",
    "compute",
    "evaluate",
    "algebra",
    "geometry",
    "trigonometry",
    "arithmetic",
    "word problem",
})

# Subjects that are predominantly numerical at the board level
_NUMERICAL_SUBJECTS: frozenset[str] = frozenset({
    "mathematics",
    "maths",
    "math",
    "physics",
    "chemistry",
})

# Action verbs in the question text that indicate computation is required
_NUMERICAL_KEYWORDS: frozenset[str] = frozenset({
    "calculate",
    "compute",
    "solve",
    "find",
    "determine",
    "evaluate",
    "simplify",
    "factorise",
    "factorize",
    "expand",
    "prove",          # mathematical proof
    "show that",
    "verify",
    "derive",
    "differentiate",
    "integrate",
    "sketch",         # geometry
    "draw",
    "construct",
    "if x",
    "if y",
    "if n",
    "find x",
    "find y",
    "find the value",
    "find the",
})

# Physical / chemical units — presence strongly implies a numerical problem
_UNIT_PATTERN = re.compile(
    r"\b(kg|g|mg|m|cm|mm|km|s|ms|min|h|hr|N|kN|J|kJ|W|kW|Pa|atm|"
    r"mol|L|mL|A|V|Ω|C|F|T|Hz|kHz|MHz|°C|°F|K|cal|kcal|"
    r"m/s|km/h|m/s²|km/s|rad/s|rad)\b",
    re.IGNORECASE,
)

# Patterns that suggest an algebraic expression or equation
_ALGEBRA_PATTERN = re.compile(
    r"(\b\d+\s*[x-z]\b"       # "3x", "2y"
    r"|\b[x-z]\s*=\s*\d"      # "x = 5"
    r"|\b[x-z]\^2\b"           # "x^2"
    r"|\d+\s*[+\-*/]\s*\d+"    # "3 + 4", "12 / 3"
    r"|=\s*\d+)",              # "= 15" (equation with result)
    re.IGNORECASE,
)


class QuestionRouter:
    """Classifies an extracted image question into a solver route.

    Usage::

        router = QuestionRouter()
        route = router.classify(extracted)   # "theory" | "numerical"
    """

    # Minimum number of signals required to override the "theory" default
    _NUMERICAL_THRESHOLD = 1

    def classify(self, extracted: "ExtractedQuestion") -> str:
        """Return the solver route for *extracted*.

        Args:
            extracted: :class:`~rag.vision_extractor.ExtractedQuestion` dict
                produced by the vision extractor.

        Returns:
            ``"numerical"`` when the question requires computation,
            ``"theory"`` otherwise (safe default).
        """
        signals = self._collect_signals(extracted)
        route = "numerical" if signals else "theory"

        log.info(
            "[ROUTER] Route: %s | signals: %s | q_type=%r subject=%r",
            route,
            signals or "none",
            extracted.get("question_type", ""),
            extracted.get("subject", ""),
        )
        return route

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _collect_signals(self, extracted: "ExtractedQuestion") -> list[str]:
        """Return a list of human-readable signal names that fired."""
        signals: list[str] = []
        question = (extracted.get("question") or "").lower()
        q_type   = (extracted.get("question_type") or "").lower().strip()
        subject  = (extracted.get("subject") or "").lower().strip()

        # ── Signal 1: question_type from vision model (highest priority) ──────
        if any(nt in q_type for nt in _NUMERICAL_QUESTION_TYPES):
            signals.append(f"question_type={q_type!r}")

        # ── Signal 2: subject ─────────────────────────────────────────────────
        if any(ns in subject for ns in _NUMERICAL_SUBJECTS):
            signals.append(f"subject={subject!r}")

        # ── Signal 3: action keyword in question text ──────────────────────────
        matched_kw = next(
            (kw for kw in _NUMERICAL_KEYWORDS if kw in question), None
        )
        if matched_kw:
            signals.append(f"keyword={matched_kw!r}")

        # ── Signal 4: physical unit detected ─────────────────────────────────
        unit_match = _UNIT_PATTERN.search(extracted.get("question") or "")
        if unit_match:
            signals.append(f"unit={unit_match.group()!r}")

        # ── Signal 5: algebraic / equation pattern ────────────────────────────
        if _ALGEBRA_PATTERN.search(question):
            signals.append("algebra_pattern")

        return signals


# Module-level singleton — import and use directly
router = QuestionRouter()
