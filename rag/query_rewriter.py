import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Follow-up detection — pure heuristic, zero API calls
# ---------------------------------------------------------------------------

_FOLLOW_UP_WORDS = {
    "it", "this", "that", "these", "those",
    "they", "them",
    "again", "more", "simpler", "shorter", "longer", "bigger",
    "expand", "elaborate",
    "example", "examples",
    "why", "how",
    "compare",
    "difference", "differences",
    "explain", "clarify",
    "simplify",
}

_FOLLOW_UP_STARTERS = {
    "it", "this", "that",
    "more", "again", "example",
    "simplify", "simpler", "bigger",
    "expand", "elaborate",
}

_SHORT_WORD_THRESHOLD = 5  # fewer than this many words → likely a follow-up


def is_follow_up(question: str) -> bool:
    """
    Return True if the question is likely a follow-up to the previous turn.

    Heuristics (fast, no API cost):
      1. Short question (<5 words) that starts with a continuation/pronoun word.
      2. The question contains a pronoun or continuation word from _FOLLOW_UP_WORDS.
    """
    tokens = question.lower().split()

    if len(tokens) < _SHORT_WORD_THRESHOLD and any(
        word in _FOLLOW_UP_STARTERS for word in tokens
    ):
        return True

    return bool(_FOLLOW_UP_WORDS.intersection(tokens))
