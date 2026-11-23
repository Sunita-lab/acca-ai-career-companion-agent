# src/rag/search.py
import chromadb

from src.rag.embed import embed_texts

CHROMA_PATH = "data/chroma"
COLLECTION = "internships"


def search_jobs(query: str, k: int = 5, where: dict | None = None) -> list[dict]:
    """Query ko embed karo, top chunks lo, aur unhe job-level par merge karo."""
    col = chromadb.PersistentClient(path=CHROMA_PATH).get_collection(COLLECTION)
    qvec = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
    res = col.query(query_embeddings=[qvec], n_results=k * 3, where=where)

    jobs: dict[str, dict] = {}
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        score = 1 - dist  # cosine similarity
        jid = meta["job_id"]
        if jid not in jobs or score > jobs[jid]["score"]:
            jobs[jid] = {**meta, "score": round(score, 3)}
    return sorted(jobs.values(), key=lambda j: j["score"], reverse=True)[:k]