from pathlib import Path
import json
import re

from sentence_transformers import SentenceTransformer
import faiss


# -----------------------------
# Configuration
# -----------------------------

KB_DIR = Path("knowledge-base")
VECTORSTORE_DIR = Path("vectorstore")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


# -----------------------------
# Load Markdown documents
# -----------------------------

def load_documents():
    documents = []

    for file_path in KB_DIR.rglob("*.md"):
        text = file_path.read_text(encoding="utf-8")

        documents.append({
            "source": str(file_path),
            "text": text
        })

    return documents


# -----------------------------
# Split document into chunks
# -----------------------------

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split Markdown content primarily by headings,
    while preventing chunks from becoming excessively large.
    """

    sections = re.split(
        r"(?=^#{1,3}\s+)",
        text,
        flags=re.MULTILINE
    )

    chunks = []

    for section in sections:

        section = section.strip()

        if not section:
            continue

        # If section is small enough, keep it intact
        if len(section) <= chunk_size:
            chunks.append(section)
            continue

        # For large sections, split by paragraphs
        paragraphs = section.split("\n\n")

        current_chunk = ""

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            candidate = (
                current_chunk + "\n\n" + paragraph
                if current_chunk
                else paragraph
            )

            if len(candidate) <= chunk_size:
                current_chunk = candidate

            else:

                if current_chunk:
                    chunks.append(current_chunk)

                # Handle extremely large paragraphs
                if len(paragraph) > chunk_size:

                    start = 0

                    while start < len(paragraph):

                        end = start + chunk_size

                        piece = paragraph[start:end].strip()

                        if piece:
                            chunks.append(piece)

                        start += chunk_size - overlap

                    current_chunk = ""

                else:
                    current_chunk = paragraph

        if current_chunk:
            chunks.append(current_chunk)

    return chunks


# -----------------------------
# Build chunks + metadata
# -----------------------------

def build_chunks(documents):
    chunks = []
    metadata = []

    for document in documents:

        document_chunks = chunk_text(document["text"])

        for index, chunk in enumerate(document_chunks):

            chunks.append(chunk)

            metadata.append({
                "source": document["source"],
                "chunk_id": index,
                "text": chunk
            })

    return chunks, metadata


# -----------------------------
# Create FAISS index
# -----------------------------

def create_vectorstore(chunks, metadata):

    print("Loading embedding model...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Creating embeddings...")

    embeddings = model.encode(
        chunks,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    VECTORSTORE_DIR.mkdir(exist_ok=True)

    faiss.write_index(
        index,
        str(VECTORSTORE_DIR / "kb.index")
    )

    with open(
        VECTORSTORE_DIR / "metadata.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("Vector store created successfully.")
    print(f"Documents : {len(set(item['source'] for item in metadata))}")
    print(f"Chunks    : {len(chunks)}")
    print(f"Dimension : {dimension}")


# -----------------------------
# Main
# -----------------------------

def main():

    print("Loading knowledge base...")

    documents = load_documents()

    print(f"Documents found: {len(documents)}")

    if not documents:
        raise RuntimeError(
            "No Markdown documents found in knowledge-base/"
        )

    chunks, metadata = build_chunks(documents)

    print(f"Chunks created: {len(chunks)}")

    create_vectorstore(chunks, metadata)


if __name__ == "__main__":
    main()