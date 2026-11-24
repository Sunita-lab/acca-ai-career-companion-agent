# scripts/eval_reasoning.py
# usage:  python scripts/eval_reasoning.py make       -> creates the rating sheet
#         python scripts/eval_reasoning.py summarize  -> averages your ratings
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.matching.retrieve import load_jobs

PROFILES_PATH = Path("data/eval/profiles.json")
MATCHING_PATH = Path("data/eval/matching_results.json")
SHEET_PATH = Path("data/eval/reasoning_rating.csv")
OUT_PATH = Path("data/eval/reasoning_results.json")

RATING_COLS = ["accuracy_1to5", "score_consistency_1to5", "clarity_1to5"]
FIELDS = ["profile_id", "position", "job_id", "job_title", "llm_score",
          "student_skills", "job_required_skills", "job_preferred_skills",
          "llm_matched", "llm_missing", "llm_reasoning"] + RATING_COLS + ["notes"]


def make() -> None:
    if SHEET_PATH.exists():
        raise SystemExit(f"{SHEET_PATH} already exists (it may hold your ratings). Delete it first to regenerate.")
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    matching = json.loads(MATCHING_PATH.read_text(encoding="utf-8"))
    jobs = load_jobs()

    rows = []
    for p in profiles:
        pid = p["id"]
        scored = sorted(matching[pid]["all_scored"], key=lambda s: (-s["score"], s["job_id"]))
        mine = list(p["profile"]["skills"]["technical"])
        for pr in p["profile"].get("projects", []):
            mine += pr.get("technologies", [])
        for position, item in (("top", scored[0]), ("bottom", scored[-1])):
            job = jobs[item["job_id"]]
            rows.append({
                "profile_id": pid, "position": position,
                "job_id": item["job_id"], "job_title": item["title"],
                "llm_score": item["score"],
                "student_skills": "; ".join(dict.fromkeys(mine)),
                "job_required_skills": "; ".join(job["required_skills"]),
                "job_preferred_skills": "; ".join(job["preferred_skills"]),
                "llm_matched": "; ".join(item["matched_skills"]),
                "llm_missing": "; ".join(item["missing_skills"]),
                "llm_reasoning": item["reasoning"],
                **{c: "" for c in RATING_COLS}, "notes": "",
            })
    with open(SHEET_PATH, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Created {SHEET_PATH} with {len(rows)} rows. Fill the 3 rating columns (1-5), save as CSV.")


def read_sheet() -> list[dict]:
    for enc in ("utf-8-sig", "cp1252"):  # Excel sometimes re-saves as cp1252
        try:
            with open(SHEET_PATH, newline="", encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise SystemExit("Could not read the CSV encoding.")


def summarize() -> None:
    rows, skipped = [], 0
    for r in read_sheet():
        try:
            vals = {c: int(r[c]) for c in RATING_COLS}
            if not all(1 <= v <= 5 for v in vals.values()):
                raise ValueError
        except (ValueError, TypeError, KeyError):
            skipped += 1
            continue
        rows.append({**r, **vals})
    if not rows:
        raise SystemExit("No fully rated rows found. Fill all 3 columns with 1-5.")
    if skipped:
        print(f"Warning: {skipped} row(s) skipped (a rating is missing or not 1-5).")

    def avg(subset, col):
        return round(sum(r[col] for r in subset) / len(subset), 2)

    result = {"rows_rated": len(rows), "overall": {c: avg(rows, c) for c in RATING_COLS}}
    result["overall"]["mean_of_three"] = round(sum(result["overall"].values()) / 3, 2)
    for pos in ("top", "bottom"):
        sub = [r for r in rows if r["position"] == pos]
        if sub:
            result[pos] = {c: avg(sub, c) for c in RATING_COLS}

    print(f"\nRows rated: {len(rows)}")
    print(f"{'':10s} " + " ".join(f"{c.replace('_1to5', ''):>20s}" for c in RATING_COLS))
    for label, sub in (("ALL", rows), ("top", [r for r in rows if r['position'] == 'top']),
                       ("bottom", [r for r in rows if r['position'] == 'bottom'])):
        if sub:
            print(f"{label:10s} " + " ".join(f"{avg(sub, c):20.2f}" for c in RATING_COLS))
    print(f"Mean of three criteria: {result['overall']['mean_of_three']}")

    low = [r for r in rows if min(r[c] for c in RATING_COLS) <= 2]
    if low:
        print("\nRows with a rating of 2 or lower (read these again):")
        for r in low:
            print(f"  {r['profile_id']} {r['job_id']} ({r['position']}): {r.get('notes', '')}")
    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "make":
        make()
    elif mode == "summarize":
        summarize()
    else:
        raise SystemExit("usage: python scripts/eval_reasoning.py make | summarize")