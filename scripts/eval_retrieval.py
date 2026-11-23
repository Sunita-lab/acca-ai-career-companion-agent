# scripts/eval_retrieval.py
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.matching.retrieve import profile_to_query
from src.profile.schema import CandidateProfile
from src.rag.search import search_jobs

JOBS_PATH = Path("data/jobs/jobs_clean.json")
PROFILES_PATH = Path("data/eval/profiles.json")
TRUTH_PATH = Path("data/eval/ground_truth.json")
OUT_PATH = Path("data/eval/retrieval_results.json")
K = 5


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def job_text(job: dict) -> str:
    # domain label is intentionally excluded, so the baseline cannot read it
    parts = [job["title"], job["description"], " ".join(job["responsibilities"]),
             " ".join(job["required_skills"]), " ".join(job["preferred_skills"]),
             " ".join(job["qualifications"])]
    return " ".join(parts)


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.avgdl = sum(len(d) for d in docs) / len(docs)
        df = Counter(t for d in docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, query: list[str], i: int) -> float:
        doc, tf, s = self.docs[i], Counter(self.docs[i]), 0.0
        for t in set(query):
            if t in tf:
                f = tf[t]
                s += self.idf[t] * f * (self.k1 + 1) / (
                    f + self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl))
        return s


def metrics(retrieved: list[str], relevant: set[str]) -> tuple[float, float]:
    hits = len(set(retrieved[:K]) & relevant)
    return hits / K, hits / len(relevant)


def main() -> None:
    jobs = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    truth = json.loads(TRUTH_PATH.read_text(encoding="utf-8"))
    bm25 = BM25([tokenize(job_text(j)) for j in jobs])

    rows, results = [], {}
    for p in profiles:
        pid = p["id"]
        relevant = set(truth[pid])
        query = profile_to_query(CandidateProfile(**p["profile"]))

        q_tokens = tokenize(query)
        ranked = sorted(range(len(jobs)), key=lambda i: bm25.score(q_tokens, i), reverse=True)
        kw_ids = [jobs[i]["job_id"] for i in ranked[:K]]
        emb_ids = [r["job_id"] for r in search_jobs(query, k=K)]

        kw_p, kw_r = metrics(kw_ids, relevant)
        em_p, em_r = metrics(emb_ids, relevant)
        rows.append((pid, len(relevant), kw_p, kw_r, em_p, em_r))
        results[pid] = {"relevant_count": len(relevant), "keyword": kw_ids, "embeddings": emb_ids,
                        "keyword_p5": kw_p, "keyword_r5": kw_r,
                        "embeddings_p5": em_p, "embeddings_r5": em_r}

    print(f"\n{'profile':20s} {'#rel':>4s} | {'KW P@5':>7s} {'KW R@5':>7s} | {'EMB P@5':>8s} {'EMB R@5':>8s}")
    for pid, n, a, b, c, d in rows:
        print(f"{pid:20s} {n:4d} | {a:7.2f} {b:7.2f} | {c:8.2f} {d:8.2f}")
    avg = lambda idx: sum(r[idx] for r in rows) / len(rows)
    print(f"{'AVERAGE':20s} {'':4s} | {avg(2):7.2f} {avg(3):7.2f} | {avg(4):8.2f} {avg(5):8.2f}")

    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()