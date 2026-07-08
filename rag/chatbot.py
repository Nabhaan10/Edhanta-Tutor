import logging
from rag.retriever import search_with_threshold
from rag.generator import generate_answer
from rag.memory import memory_manager
from rag.query_rewriter import is_follow_up

log = logging.getLogger(__name__)

# Message returned when nothing relevant is found in the vector store.
# Identical wording to the generator's system prompt so the response is
# consistent regardless of which layer catches the out-of-scope query.
_OUT_OF_SCOPE_REPLY = (
    "I couldn't find this topic in the available textbooks. "
    "Please ask a question from the Class 9 or 10 syllabus."
)


def ask(question: str, session_id: str, board: str) -> dict:
    """
    Conversational RAG pipeline.

    New questions update the session's conversation topic.  Follow-up
    questions are detected heuristically and anchor their retrieval query to
    the stored topic, preventing embedding drift across multi-turn threads.
    The *original* user message is always stored in memory so the chat
    history stays natural.

    If no relevant context is found in the vector store the refusal message
    is returned immediately — the LLM is never called for out-of-scope
    questions.

    Args:
        question:   Raw user input.
        session_id: Identifies the conversation session.
        board:      "CBSE" or "MH".

    Returns:
        {"answer": str, "sources": list[str]}
    """
    memory = memory_manager.get_memory(session_id)
    history = memory.get_history()

    # ── Follow-up detection & topic-anchored query building ──────────────────
    is_fu = is_follow_up(question) and bool(history)
    if is_fu:
        topic = memory.get_topic()
        search_query = f"{topic} {question}".strip() if topic else question
        log.info("[TOPIC] Follow-up. Topic: %r | Query: %r", topic, search_query)
    else:
        # New topic — store it and search with the question as-is
        memory.set_topic(question)
        search_query = question
        log.info("[TOPIC] New topic set: %r", question)

    log.info("[HISTORY] History size: %d messages", len(history))

    # ── Retrieval with relevance filtering ────────────────────────────────────
    results = search_with_threshold(search_query)

    # ── Out-of-scope guard — short-circuit before calling the LLM ────────────
    if not results["documents"][0]:
        log.info("[GUARD] No relevant context found — returning out-of-scope reply.")
        # Still store the exchange in memory so follow-up detection works
        memory.add_user_message(question)
        memory.add_assistant_message(_OUT_OF_SCOPE_REPLY)
        return {
            "answer": _OUT_OF_SCOPE_REPLY,
            "sources": [],
        }

    context = "\n\n".join(results["documents"][0])
    sources = list({
        metadata["source"]
        for metadata in results["metadatas"][0]
    })

    # ── Generation ───────────────────────────────────────────────────────────
    # Always pass the expanded search_query so the generator has full context
    # for follow-ups without needing a separate rewriter call.
    generation_question = search_query
    answer = generate_answer(generation_question, context, history, board)

    # ── Memory update (always store original user message) ───────────────────
    memory.add_user_message(question)
    memory.add_assistant_message(answer)

    return {
        "answer": answer,
        "sources": sources,
    }
