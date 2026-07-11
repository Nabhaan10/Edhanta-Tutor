from fastembed import TextEmbedding

from config import EMBEDDING_MODEL

# fastembed uses ONNX Runtime instead of PyTorch — ~10x lighter on memory.
# "sentence-transformers/all-MiniLM-L6-v2" is the fastembed equivalent of
# the all-MiniLM-L6-v2 model previously used via sentence-transformers.
model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")


def encode(text: str) -> list[float]:
    """Encode a single string into an embedding vector."""
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()