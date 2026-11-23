# scripts/build_index.py
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb
from src.rag.chunking import chunk_job
from src.rag.embed import embed_texts

JOBS_PATH = Path("data/jobs/jobs_clean.json")
CHROMA_PATH = "data/chroma"
COLLECTION = "internships"


def main() -> None:
    jobs = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    chunks = [c for job in jobs for c in chunk_job(job)]
    print(f"{len(jobs)} postings -> {len(chunks)} chunks")

    print("Embedding chunks (kuch minute lag sakte hain)...")
    vectors = embed_texts([c["text"] for c in chunks], task_type="RETRIEVAL_DOCUMENT")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(COLLECTION)  # rebuild from scratch
    except Exception:  # noqa: BLE001
        pass
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    for i in range(0, len(chunks), 100):
        part = chunks[i : i + 100]
        col.add(
            ids=[c["id"] for c in part],
            embeddings=vectors[i : i + 100],
            documents=[c["text"] for c in part],
            metadatas=[c["metadata"] for c in part],
        )
    print(f"Indexed {col.count()} chunks in '{COLLECTION}' -> {CHROMA_PATH}")


if __name__ == "__main__":
    main()