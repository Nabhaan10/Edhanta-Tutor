import json
from pathlib import Path
from rag.embedding_model import model

import chromadb

from config import CHROMA_DB_PATH, COLLECTION_NAME

CHUNKS_DIR = Path("data/chunks")

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


def load_chunks():

    all_chunks = []

    for json_file in CHUNKS_DIR.rglob("*.json"):

        with open(json_file, "r", encoding="utf-8") as file:

            chunks = json.load(file)

            all_chunks.extend(chunks)

    return all_chunks

def store_chunks(chunks):

    for chunk in chunks:

        embedding = model.encode(
            chunk["text"]
        ).tolist()

        metadata = {
            key: value
            for key, value in chunk.items()
            if key not in ("id", "text")
        }

        collection.add(
            ids=[chunk["id"]],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[metadata]
        )


if __name__ == "__main__":

    chunks = load_chunks()

    print(f"Loaded {len(chunks)} chunks")

    store_chunks(chunks)

    print("Stored in ChromaDB")