import json
import os
import pickle

import faiss
import numpy as np
from sentence_transformers import (
    SentenceTransformer
)


INPUT_FILE = (
    "data/processed/clean_assessments.json"
)

FAISS_INDEX_FILE = (
    "data/faiss/assessment_index.faiss"
)

METADATA_FILE = (
    "data/faiss/assessment_metadata.pkl"
)


os.makedirs(
    "data/faiss",
    exist_ok=True
)


def load_data():
    print("Loading dataset...")

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    print(
        f"Loaded {len(data)} assessments"
    )

    return data


def build_embeddings(
    assessments,
    model
):
    print("Generating embeddings...")

    texts = [
        item["search_text"]
        for item in assessments
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    print(
        f"Embedding shape: {embeddings.shape}"
    )

    return embeddings


def main():
    assessments = load_data()

    print("Loading embedding model...")

    model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    embeddings = build_embeddings(
        assessments,
        model
    )

    dimension = embeddings.shape[1]

    print("Building FAISS index...")

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings)

    print(
        f"FAISS index contains {index.ntotal} vectors"
    )

    faiss.write_index(
        index,
        FAISS_INDEX_FILE
    )

    with open(
        METADATA_FILE,
        "wb"
    ) as f:
        pickle.dump(
            assessments,
            f
        )

    print("DONE")


if __name__ == "__main__":
    main()