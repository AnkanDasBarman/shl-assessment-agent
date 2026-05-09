import json
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


INPUT_FILE = "data/processed/clean_assessments.json"

FAISS_INDEX_FILE = "data/faiss/assessment_index.faiss"

METADATA_FILE = "data/faiss/assessment_metadata.pkl"


def load_dataset():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_embeddings(texts, model):
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    return np.array(
        embeddings,
        dtype="float32"
    )


def main():
    print("Loading dataset...")

    assessments = load_dataset()

    print(f"Loaded {len(assessments)} assessments")

    texts = [
        item["search_text"]
        for item in assessments
    ]

    print("Loading embedding model...")

    model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    print("Generating embeddings...")

    embeddings = build_embeddings(
        texts,
        model
    )

    print(
        f"Embedding shape: {embeddings.shape}"
    )

    dimension = embeddings.shape[1]

    print("Building FAISS index...")

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    print(
        f"FAISS index contains {index.ntotal} vectors"
    )

    faiss.write_index(
        index,
        FAISS_INDEX_FILE
    )

    with open(METADATA_FILE, "wb") as f:
        pickle.dump(assessments, f)

    print("DONE")


if __name__ == "__main__":
    main()