import os
import pickle
import subprocess

import faiss
import numpy as np
from sentence_transformers import (
    SentenceTransformer
)


FAISS_INDEX_FILE = (
    "data/faiss/assessment_index.faiss"
)

METADATA_FILE = (
    "data/faiss/assessment_metadata.pkl"
)


if not os.path.exists(
    FAISS_INDEX_FILE
):
    print("FAISS index missing...")
    print("Building embeddings...")

    subprocess.run(
        ["python3", "scripts/build_embeddings.py"],
        check=True
    )


print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


print("Loading FAISS index...")

index = faiss.read_index(
    FAISS_INDEX_FILE
)


print("Loading metadata...")

with open(METADATA_FILE, "rb") as f:
    metadata = pickle.load(f)


print(
    f"Loaded {len(metadata)} assessments"
)


def search_assessments(
    query,
    top_k=5
):
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    query_embedding = np.array(
        query_embedding,
        dtype="float32"
    )

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for idx in indices[0]:
        item = metadata[idx]

        results.append({
            "name": item["name"],
            "url": item["url"],
            "description": item["description"],
            "categories": item["categories"],
        })

    return results


if __name__ == "__main__":
    query = input(
        "Enter search query: "
    )

    results = search_assessments(
        query
    )

    print("\nTop Results:\n")

    for i, item in enumerate(
        results,
        start=1
    ):
        print(
            f"{i}. {item['name']}"
        )

        print(item["url"])

        print(item["categories"])

        print()