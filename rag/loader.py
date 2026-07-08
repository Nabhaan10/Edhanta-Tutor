import fitz
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def extract_text(pdf_path: Path):
    document = fitz.open(pdf_path)

    text = ""


    for page in document:
        text += page.get_text()

    document.close()

    return text


def save_text(text: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(text)


def process_all_pdfs():
    pdfs = RAW_DIR.rglob("*.pdf")

    count = 0

    for pdf in pdfs:
        print(f"Processing: {pdf}")

        text = extract_text(pdf)

        output_path = PROCESSED_DIR / pdf.relative_to(RAW_DIR)
        output_path = output_path.with_suffix(".txt")

        save_text(text, output_path)

        count += 1

    print(f"\nProcessed {count} PDFs successfully.")


if __name__ == "__main__":
    process_all_pdfs()