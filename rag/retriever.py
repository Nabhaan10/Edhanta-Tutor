import logging

import chromadb
from rag.embedding_model import model

from config import CHROMA_DB_PATH, COLLECTION_NAME, SCOPE_THRESHOLD, CONTEXT_THRESHOLD

log = logging.getLogger(__name__)

# Create the ChromaDB client and collection ONCE at startup, not per request.
# Creating a new PersistentClient on every call opens a new SQLite connection
# and competes for file locks. On Windows/OneDrive this causes requests to
# hang indefinitely. A module-level singleton avoids this entirely.
_chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
_collection = _chroma_client.get_collection(COLLECTION_NAME)


def search(query: str, n_results: int = 5) -> dict:
    """Search the vector database for chunks relevant to the query.

    Args:
        query:     The user's question as a plain string.
        n_results: Number of top results to return (default 5).

    Returns:
        A ChromaDB results dict with keys: 'documents', 'metadatas',
        'distances', and 'ids'.

    Raises:
        RuntimeError: If embedding or database query fails.
    """
    try:
        print(f"\nSearching for: {query}")
        print(f"\nCollection count: {_collection.count()}")
        print(f"DB Path: {CHROMA_DB_PATH}")
        print(f"Collection: {COLLECTION_NAME}")

        query_embedding = model.encode(query).tolist()

        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        print("Retrieved sources:")
        for m in results["metadatas"][0]:
            print("-", m["source"])

        return None
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve results: {e}") from e


def search_with_threshold(query: str, n_results: int = 5) -> dict:
    """Search the vector database with production-ready two-threshold filtering.

    Design rationale
    ----------------
    The old approach applied a single threshold to *every* retrieved chunk and
    rejected the query if any chunk failed.  This caused false negatives:
    ChromaDB always returns exactly ``n_results`` chunks even for fully
    in-scope queries, and the tail chunks (rank 4-5) are routinely less
    relevant than the top hits.  Rejecting on the worst match penalises
    legitimate questions unfairly.

    This implementation uses two separate thresholds with distinct roles:

    1. **Scope gate** (``SCOPE_THRESHOLD``, from config.py)
       Evaluated against the *single best* (lowest) distance only.
       • If ``best_distance > SCOPE_THRESHOLD`` → the query has no relevant
         match anywhere in the corpus → return empty → chatbot short-circuits.
       • A strong top hit (low distance) always passes, regardless of how
         poor the tail chunks are.

    2. **Context trim** (``CONTEXT_THRESHOLD``, from config.py)
       Applied *only after* the scope gate passes.
       • Strips individual tail chunks whose distance exceeds the looser
         context threshold — they add noise without adding signal to the LLM.
       • Never causes a rejection on its own.
       • ``CONTEXT_THRESHOLD`` should always be >= ``SCOPE_THRESHOLD``.

    Why this eliminates false negatives
    ------------------------------------
    "What is inertia?" retrieves chunk #1 at distance ~0.4.  The scope gate
    passes (0.4 < 1.0).  Chunks #4-5 at distance ~1.1 are stripped by the
    context trim but do NOT veto the query.  Result: correct answer returned.

    "Bellman-Ford algorithm" retrieves chunk #1 at distance ~1.3.  The scope
    gate fires (1.3 > 1.0).  Result: out-of-scope reply, no LLM call.

    Args:
        query:     The user's question as a plain string.
        n_results: Maximum number of candidates to fetch before filtering.

    Returns:
        ChromaDB-style results dict.  Each inner list may be shorter than
        ``n_results`` after context trimming, and will be empty (all four
        lists) if the scope gate fires.
    """
    raw = search(query, n_results=n_results)

    docs      = raw["documents"][0]
    metas     = raw["metadatas"][0]
    distances = raw["distances"][0]
    ids       = raw["ids"][0]

    # ── Debug: always log all distances ───────────────────────────────────────
    distance_summary = " | ".join(
        f"#{i+1} {round(d, 4)}" for i, d in enumerate(distances)
    )
    log.info("[RETRIEVER] Query: %r", query)
    log.info("[RETRIEVER] Distances  → %s", distance_summary)
    log.info(
        "[RETRIEVER] Thresholds → scope: %.2f  context: %.2f",
        SCOPE_THRESHOLD, CONTEXT_THRESHOLD,
    )

    # ── 1. Scope gate: decision based on the single BEST match ────────────────
    # ChromaDB returns results sorted by distance ascending, so distances[0]
    # is always the best, but we use min() to be defensive.
    best_distance = min(distances) if distances else float("inf")
    log.info("[RETRIEVER] Best distance: %.4f", best_distance)

    if best_distance > SCOPE_THRESHOLD:
        log.info(
            "[RETRIEVER] REJECTED — best %.4f > scope threshold %.2f",
            best_distance, SCOPE_THRESHOLD,
        )
        return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    # ── 2. Context trim: strip noisy tail chunks (never causes rejection) ─────
    kept = [
        (doc, meta, dist, id_)
        for doc, meta, dist, id_ in zip(docs, metas, distances, ids)
        if dist <= CONTEXT_THRESHOLD
    ]

    log.info(
        "[RETRIEVER] PASSED — %d/%d chunks kept after context trim (threshold %.2f)",
        len(kept), len(docs), CONTEXT_THRESHOLD,
    )

    if kept:
        f_docs, f_metas, f_dists, f_ids = zip(*kept)
    else:
        # Scope gate passed but every chunk exceeded the context threshold.
        # This can only happen if CONTEXT_THRESHOLD < SCOPE_THRESHOLD
        # (a misconfiguration). Fall back to the single best chunk so the
        # LLM still has something to work with.
        log.warning(
            "[RETRIEVER] Context trim removed all chunks despite scope gate passing. "
            "Check CONTEXT_THRESHOLD >= SCOPE_THRESHOLD in config.py. "
            "Falling back to best chunk only."
        )
        best_idx = distances.index(min(distances))
        f_docs  = (docs[best_idx],)
        f_metas = (metas[best_idx],)
        f_dists = (distances[best_idx],)
        f_ids   = (ids[best_idx],)

    return {
        "documents": [list(f_docs)],
        "metadatas": [list(f_metas)],
        "distances": [list(f_dists)],
        "ids":       [list(f_ids)],
    }


if __name__ == "__main__":

    query = input("Ask a question: ")

    results = search(query)

    for i in range(len(results["documents"][0])):

        metadata = results["metadatas"][0][i]

        print(f"\n========== Result {i+1} ==========")
        print(f"Class   : {metadata['class']}")
        print(f"Subject : {metadata['subject']}")
        print(f"Source  : {metadata['source']}")
        print("\n")
        print(results["documents"][0][i])
        print("\n" + "=" * 60)