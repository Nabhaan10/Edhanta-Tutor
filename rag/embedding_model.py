from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL

model = None
# model = SentenceTransformer(
#     EMBEDDING_MODEL,
#     local_files_only=True
# )