# scripts/eval_matching.py
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.matching.agent import match_profile
from src.profile.schema import CandidateProfile

PROFILES_PATH = Path("data/eval/profiles.json")
TRUTH_PATH = Path("data/eval/ground_truth.json")
RETRIEVAL_PATH = Path("data/eval/retrieval_results.json")
OUT_PATH = Path("data/eval/matching_results.json")
K = 5


def main() -> None:
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    truth = json.loads(TRUTH_PATH.read_text(encoding="utf-8"))
    retrieval = json.loads(RETRIEVAL_PATH.read_text(encoding="utf-8"))
    results = json.loads(OUT_PATH.read_text(encoding="utf-8")) if OUT_PATH.exists() else {}

    for p in profiles:
        pid = p["id"]
        if pid in results:
            print(f"{pid}: already done, skipping")
            continue
        relevant = set(truth[pid])
        print(f"Matching {pid}...")
        ranked = match_profile(CandidateProfile(**p["profile"]), k=10, workers=1)
        if len(ranked) < 10:
            print(f"{pid}: only {len(ranked)}/10 jobs scored, not saved. Run again to retry.")
            break

        top_ids = [r["job"]["job_id"] for r in ranked[:K]]
        hits = len(set(top_ids) & relevant)
        results[pid] = {
            "top5": top_ids,
            "precision5": hits / K,
            "recall5": hits / len(relevant),
            "all_scored": [
                {
                    "job_id": r["job"]["job_id"],
                    "title": r["job"]["title"],
                    "score": r["match"].score,
                    "matched_skills": r["match"].matched_skills,
                    "missing_skills": r["match"].missing_skills,
                    "reasoning": r["match"].reasoning,
                }
                for r in ranked
            ],
        }
        OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{pid}: saved")

    done = [p["id"] for p in profiles if p["id"] in results]
    if not done:
        return
    print(f"\n{'profile':20s} | {'P@5: KW':>8s} {'EMB':>6s} {'EMB+LLM':>8s} | {'R@5: KW':>8s} {'EMB':>6s} {'EMB+LLM':>8s}")
    rows = []
    for pid in done:
        r, m = retrieval[pid], results[pid]
        row = (r["keyword_p5"], r["embeddings_p5"], m["precision5"],
               r["keyword_r5"], r["embeddings_r5"], m["recall5"])
        rows.append(row)
        print(f"{pid:20s} | {row[0]:8.2f} {row[1]:6.2f} {row[2]:8.2f} | {row[3]:8.2f} {row[4]:6.2f} {row[5]:8.2f}")
    avg = [sum(r[i] for r in rows) / len(rows) for i in range(6)]
    print(f"{'AVERAGE':20s} | {avg[0]:8.2f} {avg[1]:6.2f} {avg[2]:8.2f} | {avg[3]:8.2f} {avg[4]:6.2f} {avg[5]:8.2f}")
    print(f"\nProfiles done: {len(done)}/{len(profiles)}")


if __name__ == "__main__":
    main()