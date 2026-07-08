import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

PROCESSED_DIR = Path("data/processed")
CHUNKS_DIR = Path("data/chunks")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)

def chunk_file(txt_file: Path):
    with open(txt_file, "r", encoding="utf-8") as file:
        text = file.read()

    chunks = splitter.split_text(text)

    return chunks

def build_chunk_objects(txt_file: Path, chunks):
    subject_folder = txt_file.parent.name

    class_number = int(subject_folder.split("_")[0].replace("class", ""))
    subject = subject_folder.split("_")[1].capitalize()
    chapter = txt_file.stem.lower().replace(" ", "_")

    documents = []

    for index, chunk in enumerate(chunks):

        chunk_data = {
            "id": f"class{class_number}_{subject.lower()}_{chapter}_{index + 1}",
            "text": chunk,
            "source": txt_file.with_suffix(".pdf").name,
            "class": class_number,
            "subject": subject,
        }

        documents.append(chunk_data)

    return documents

def save_chunks(txt_file: Path, documents):

    output_folder = CHUNKS_DIR / txt_file.parent.relative_to(PROCESSED_DIR)

    output_folder.mkdir(parents=True, exist_ok=True)

    output_file = output_folder / f"{txt_file.stem}.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(documents, file, indent=4, ensure_ascii=False)

def process_all_files():

    txt_files = PROCESSED_DIR.rglob("*.txt")

    total_chunks = 0

    for txt_file in txt_files:

        chunks = chunk_file(txt_file)

        documents = build_chunk_objects(txt_file, chunks)

        save_chunks(txt_file, documents)

        total_chunks += len(documents)

        print(f"{txt_file.name} -> {len(documents)} chunks")

    print(f"\nTotal chunks created: {total_chunks}")


if __name__ == "__main__":
    process_all_files()