# scripts/eval_consistency.py
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.matching.retrieve import load_jobs
from src.matching.score import score_job
from src.profile.schema import CandidateProfile

PROFILES_PATH = Path("data/eval/profiles.json")
MATCHING_PATH = Path("data/eval/matching_results.json")
OUT_PATH = Path("data/eval/consistency_results.json")
PROFILE_IDS = ["P1_ml", "P4_cybersecurity"]
NEW_RUNS = 2  # Run 1 = scores already saved by eval_matching.py


def ranking(scores: dict[str, int]) -> list[str]:
    # ties are broken by job_id, so equal scores never count as a rank change
    return sorted(scores, key=lambda j: (-scores[j], j))


def main() -> None:
    profiles = {p["id"]: p for p in json.loads(PROFILES_PATH.read_text(encoding="utf-8"))}
    matching = json.loads(MATCHING_PATH.read_text(encoding="utf-8"))
    jobs = load_jobs()
    results = json.loads(OUT_PATH.read_text(encoding="utf-8")) if OUT_PATH.exists() else {}

    for pid in PROFILE_IDS:
        if pid in results:
            print(f"{pid}: already done, skipping")
            continue
        profile = CandidateProfile(**profiles[pid]["profile"])
        top5 = matching[pid]["top5"]
        saved = {s["job_id"]: s["score"] for s in matching[pid]["all_scored"]}
        runs = [{j: saved[j] for j in top5}]

        try:
            for n in range(NEW_RUNS):
                print(f"{pid}: run {n + 2}/{NEW_RUNS + 1}")
                runs.append({j: score_job(profile, jobs[j]).score for j in top5})
        except RuntimeError as e:
            print(f"{pid}: stopped ({e}). Not saved. Run again to retry.")
            break

        per_job = {}
        for j in top5:
            vals = [r[j] for r in runs]
            per_job[j] = {"scores": vals, "range": max(vals) - min(vals),
                          "std": round(statistics.pstdev(vals), 2)}
        results[pid] = {
            "per_job": per_job,
            "avg_range": round(sum(v["range"] for v in per_job.values()) / len(top5), 2),
            "max_range": max(v["range"] for v in per_job.values()),
            "identical_jobs": sum(1 for v in per_job.values() if v["range"] == 0),
            "same_ranking": len({tuple(ranking(r)) for r in runs}) == 1,
            "same_top1": len({ranking(r)[0] for r in runs}) == 1,
        }
        OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"{pid}: saved")

    if not results:
        return
    print("\nRun 1 = saved scores from eval_matching.py, runs 2-3 = new")
    for pid, r in results.items():
        print(f"\n{pid}")
        for j, v in r["per_job"].items():
            print(f"  {j}: scores {v['scores']}  range {v['range']}  std {v['std']}")
        print(f"  avg range {r['avg_range']} | max range {r['max_range']} | "
              f"identical {r['identical_jobs']}/5 | same ranking: {r['same_ranking']} | same top-1: {r['same_top1']}")


if __name__ == "__main__":
    main()