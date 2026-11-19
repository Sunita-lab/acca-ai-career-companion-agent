# scripts/clean_jobs.py
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.jobs.schema import JobPosting

IN_PATH = Path("data/jobs/jobs_raw.json")
OUT_PATH = Path("data/jobs/jobs_clean.json")
REPORT_PATH = Path("data/jobs/cleaning_report.json")

INTERN_WORDS = ("intern", "trainee", "apprentice")
JACCARD_THRESHOLD = 0.8


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def words(text: str) -> set[str]:
    return set(norm(text).split())


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def clean_skills(skills: list[str]) -> list[str]:
    seen, out = set(), []
    for s in skills:
        s = s.strip()
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


def incomplete_reason(job: dict) -> str | None:
    if len(job["required_skills"]) < 3:
        return "fewer than 3 required skills"
    if len(job["responsibilities"]) < 2:
        return "fewer than 2 responsibilities"
    if len(job["description"].split()) < 15:
        return "description too short"
    if not job.get("education_required") or not job.get("experience_required"):
        return "missing education/experience requirement"
    return None


def main() -> None:
    raw = json.loads(IN_PATH.read_text(encoding="utf-8"))
    removed: list[dict] = []
    kept: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()

    for item in raw:
        job_id = item.get("job_id", "?")

        # 1. schema validation
        try:
            job = JobPosting(**item).model_dump()
        except Exception as e:  # noqa: BLE001
            removed.append({"job_id": job_id, "reason": f"invalid schema: {e}"})
            continue

        job["required_skills"] = clean_skills(job["required_skills"])
        job["preferred_skills"] = clean_skills(job["preferred_skills"])

        # 2. incomplete
        reason = incomplete_reason(job)
        if reason:
            removed.append({"job_id": job_id, "reason": f"incomplete: {reason}"})
            continue

        # 3. irrelevant (not an internship)
        text = f"{job['title']} {job['description']}".lower()
        if not any(w in text for w in INTERN_WORDS):
            removed.append({"job_id": job_id, "reason": "irrelevant: not an internship"})
            continue

        # 4a. exact duplicate (same title + company)
        key = (norm(job["title"]), norm(job["company"]))
        if key in seen_keys:
            removed.append({"job_id": job_id, "reason": "duplicate: same title + company"})
            continue

        # 4b. near duplicate (very similar description + skills)
        sig = words(job["description"]) | words(" ".join(job["required_skills"]))
        dup_of = next(
            (k["job_id"] for k in kept
             if k["domain"] == job["domain"]
             and jaccard(sig, words(k["description"]) | words(" ".join(k["required_skills"]))) >= JACCARD_THRESHOLD),
            None,
        )
        if dup_of:
            removed.append({"job_id": job_id, "reason": f"duplicate: near-identical to {dup_of}"})
            continue

        seen_keys.add(key)
        kept.append(job)

    OUT_PATH.write_text(json.dumps(kept, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(
        json.dumps({"raw": len(raw), "kept": len(kept), "removed": removed}, indent=2),
        encoding="utf-8",
    )

    print(f"Raw: {len(raw)} | Kept: {len(kept)} | Removed: {len(removed)}")
    print("\nRemoval reasons:")
    for reason, n in Counter(r["reason"].split(":")[0] + ":" + r["reason"].split(":")[1][:30] if ":" in r["reason"] else r["reason"] for r in removed).most_common():
        print(f"  {n:3d}  {reason}")
    print("\nPer domain:")
    for d, n in sorted(Counter(j["domain"] for j in kept).items()):
        print(f"  {n:3d}  {d}")
    print("\nPer location:")
    for loc, n in Counter(j["location"] for j in kept).most_common():
        print(f"  {n:3d}  {loc}")
    print(f"\nSaved: {OUT_PATH} and {REPORT_PATH}")


if __name__ == "__main__":
    main()