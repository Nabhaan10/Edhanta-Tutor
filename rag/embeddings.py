from pathlib import Path
from rag.embedding_model import encode

CHUNKS_DIR = Path("data/chunks")


def create_embedding(text: str):
    return encode(text)

def process_all_chunks():
    for file in CHUNKS_DIR.rglob("*.txt"):
        print(file)