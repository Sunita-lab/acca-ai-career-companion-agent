# scripts/build_ground_truth.py
import json
import re
from pathlib import Path

JOBS_PATH = Path("data/jobs/jobs_clean.json")
PROFILES_PATH = Path("data/eval/profiles.json")
OUT_PATH = Path("data/eval/ground_truth.json")
MIN_SKILL_OVERLAP = 2


def norm(skill: str) -> str:
    """'Scikit-Learn' and 'scikit-learn' -> 'scikitlearn'; 'Power BI' and 'PowerBI' -> 'powerbi'."""
    return re.sub(r"[^a-z0-9]", "", skill.lower())


def main() -> None:
    jobs = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))

    truth = {}
    for p in profiles:
        student_skills = {norm(s) for s in p["profile"]["skills"]["technical"]}
        relevant = []
        for job in jobs:
            if job["domain"] not in p["expected_domains"]:
                continue
            job_skills = {norm(s) for s in job["required_skills"] + job["preferred_skills"]}
            overlap = student_skills & job_skills
            if len(overlap) >= MIN_SKILL_OVERLAP:
                relevant.append(job["job_id"])
        truth[p["id"]] = relevant
        in_domain = sum(1 for j in jobs if j["domain"] in p["expected_domains"])
        print(f"{p['id']:20s} relevant: {len(relevant):3d}  (jobs in expected domains: {in_domain})")

    OUT_PATH.write_text(json.dumps(truth, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()