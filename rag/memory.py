from collections import deque


class ConversationMemory:
    """Sliding-window conversation history + persistent topic anchor.

    The *topic* is set once when a new (non-follow-up) question arrives and
    stays fixed for all subsequent follow-ups in the same thread.  This
    prevents embedding drift where chaining follow-up queries together
    ("Give an example. Explain it simply.") pulls ChromaDB away from the
    original subject.
    """

    def __init__(self, max_messages: int = 8):
        self._history = deque(maxlen=max_messages)
        self._topic: str = ""  # the current conversation topic

    # ── History ──────────────────────────────────────────────────────────────

    def add_user_message(self, message: str):
        self._history.append({
            "role": "user",
            "content": message
        })

    def add_assistant_message(self, message: str):
        self._history.append({
            "role": "assistant",
            "content": message
        })

    def get_history(self):
        return list(self._history)

    # ── Topic ─────────────────────────────────────────────────────────────────

    def set_topic(self, question: str) -> None:
        """Store the question as the current conversation topic.

        Call this ONLY when a genuinely new (non-follow-up) question arrives.
        """
        self._topic = question

    def get_topic(self) -> str:
        """Return the current conversation topic, or empty string if none."""
        return self._topic

    def clear(self):
        self._history.clear()
        self._topic = ""

class MemoryManager:

    def __init__(self):
        self._sessions = {}

    def get_memory(self, session_id: str):

        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationMemory()

        return self._sessions[session_id]

memory_manager = MemoryManager()