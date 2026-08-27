from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer


# --------------------------------
# Configuration
# --------------------------------

VECTORSTORE_DIR = Path("vectorstore")

INDEX_PATH = VECTORSTORE_DIR / "kb.index"
METADATA_PATH = VECTORSTORE_DIR / "metadata.json"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TOP_K = 3


# --------------------------------
# Load vector store
# --------------------------------

def load_vectorstore():

    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {INDEX_PATH}\n"
            "Run ingest.py first."
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_PATH}\n"
            "Run ingest.py first."
        )

    index = faiss.read_index(str(INDEX_PATH))

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    return index, metadata


# --------------------------------
# Load embedding model
# --------------------------------

def load_model():

    print("Loading embedding model...")

    return SentenceTransformer(EMBEDDING_MODEL)


# --------------------------------
# Retrieve relevant KB chunks
# --------------------------------

def retrieve(query, model, index, metadata, top_k=TOP_K):

    # Convert query into embedding
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    # Search FAISS
    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, index_id in zip(scores[0], indices[0]):

        # Ignore invalid FAISS results
        if index_id == -1:
            continue

        result = metadata[index_id].copy()

        result["score"] = float(score)

        results.append(result)

    return results


# --------------------------------
# Display results
# --------------------------------

def display_results(query, results):

    print()
    print("=" * 70)
    print("QUERY")
    print("=" * 70)

    print(query)

    print()
    print("=" * 70)
    print("RETRIEVED KNOWLEDGE BASE")
    print("=" * 70)

    if not results:
        print("No relevant documents found.")
        return

    for position, result in enumerate(results, start=1):

        print()
        print(f"RESULT {position}")
        print("-" * 70)

        print(f"Similarity Score : {result['score']:.4f}")
        print(f"Source           : {result['source']}")
        print(f"Chunk ID          : {result['chunk_id']}")

        print()
        print("Content:")
        print(result["text"])


# --------------------------------
# Main
# --------------------------------

def main():

    print("Initializing RAG retriever...")

    index, metadata = load_vectorstore()

    model = load_model()

    print("RAG retriever ready.")

    print()
    print("Type a support question.")
    print("Type 'exit' to stop.")

    while True:

        query = input("\nQuestion: ").strip()

        if query.lower() == "exit":
            print("Exiting...")
            break

        if not query:
            print("Please enter a question.")
            continue

        results = retrieve(
            query=query,
            model=model,
            index=index,
            metadata=metadata,
            top_k=TOP_K
        )

        display_results(query, results)


if __name__ == "__main__":
    main()