MODEL_NAME = "openai/gpt-4o-mini"   # OpenRouter model — change freely
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_SITE_URL = "http://localhost:3000"   # shown in OpenRouter dashboard
OPENROUTER_SITE_NAME = "Edhanta Tutor"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

COLLECTION_NAME = "edhanta"

CHROMA_DB_PATH = "chroma_db"

# ── Relevance filtering (two-threshold design) ────────────────────────────────
#
# ChromaDB cosine distances: 0.0 = identical vectors, 2.0 = opposite vectors.
# Typical in-syllabus queries score  0.2 – 0.8 on the best chunk.
# Typical out-of-syllabus queries score 1.0+ even on the best chunk.
#
# SCOPE_THRESHOLD   — Gate on the single BEST retrieved chunk.
#   • If best_distance > SCOPE_THRESHOLD → query is out-of-scope → reject early.
#   • Decision is based on one number, not the average, so a strong first hit
#     always lets the query through even if later chunks are noisy.
#   • Raise this value to be more permissive; lower it to be stricter.
#
# CONTEXT_THRESHOLD — Secondary filter applied AFTER the scope check passes.
#   • Chunks with distance > CONTEXT_THRESHOLD are stripped from the context
#     window fed to the LLM (they add noise without adding signal).
#   • Never causes a rejection on its own — it only prunes the context.
#   • Should always be >= SCOPE_THRESHOLD.
#
SCOPE_THRESHOLD   = 1.2   # reject if best match is worse than this
CONTEXT_THRESHOLD = 1.4   # strip individual chunks worse than this from context