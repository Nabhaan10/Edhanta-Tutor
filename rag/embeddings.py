from sentence_transformers import SentenceTransformer
from pathlib import Path

CHUNKS_DIR = Path("data/chunks")

model = SentenceTransformer("all-MiniLM-L6-v2")

def create_embedding(text: str):
    return model.encode(text)

def process_all_chunks():
    for file in CHUNKS_DIR.rglob("*.txt"):
        print(file)