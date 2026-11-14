"""Evaluate the LLM resume parser against ground-truth JSON.

Usage (from project root):
    python scripts/test_parser.py        # first 5 resumes
    python scripts/test_parser.py 10     # first 10 resumes
"""
import json
import sys
import time
from pathlib import Path

# make `src` importable when running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.resume_parser.extract_text import extract_text_from_pdf
from src.resume_parser.parse_resume import parse_resume

RESUME_DIR = Path(__file__).resolve().parent.parent / "data" / "resumes"
DELAY_SECONDS = 4  # be gentle with the free tier


def norm(s) -> str:
    return " ".join(str(s).lower().split())


def prf(pred: set, truth: set):
    """Precision, recall, F1 for two sets."""
    if not pred and not truth:
        return 1.0, 1.0, 1.0
    tp = len(pred & truth)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(truth) if truth else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def evaluate(profile, truth: dict) -> dict:
    pred_skills = {norm(s) for s in profile.skills.technical + profile.skills.soft}
    true_skills = {norm(s) for s in truth["skills"]}

    pred_proj = {norm(p.title) for p in profile.projects}
    true_proj = {norm(p["title"]) for p in truth["projects"]}

    pred_org = {norm(e.organization) for e in profile.experience}
    true_org = {norm(e["company"]) for e in truth["experience"]}

    pred_inst = {norm(e.institution) for e in profile.education}
    true_inst = {norm(e["institute"]) for e in truth["education"]}

    return {
        "name": norm(profile.name) == norm(truth["name"]),
        "email": norm(profile.email or "") == norm(truth["email"]),
        "phone": norm(profile.phone or "") == norm(truth["phone"]),
        "skills_f1": prf(pred_skills, true_skills)[2],
        "projects_f1": prf(pred_proj, true_proj)[2],
        "experience_f1": prf(pred_org, true_org)[2],
        "education_f1": prf(pred_inst, true_inst)[2],
        "_skills_missing": sorted(true_skills - pred_skills),
        "_skills_extra": sorted(pred_skills - true_skills),
    }


def main(n: int) -> None:
    results = []
    for i in range(1, n + 1):
        stem = f"resume_{i:02d}"
        pdf_path = RESUME_DIR / f"{stem}.pdf"
        json_path = RESUME_DIR / f"{stem}.json"
        if not pdf_path.exists() or not json_path.exists():
            print(f"{stem}: file missing, skipped")
            continue

        truth = json.loads(json_path.read_text(encoding="utf-8"))
        with open(pdf_path, "rb") as f:
            text = extract_text_from_pdf(f)

        try:
            profile = parse_resume(text)
            res = evaluate(profile, truth)
        except Exception as e:  # noqa: BLE001
            print(f"{stem}: parsing FAILED -> {e}")
            continue

        results.append(res)
        print(
            f"{stem}: name={res['name']} email={res['email']} phone={res['phone']} | "
            f"skills F1={res['skills_f1']:.2f} projects F1={res['projects_f1']:.2f} "
            f"exp F1={res['experience_f1']:.2f} edu F1={res['education_f1']:.2f}"
        )
        if res["_skills_missing"] or res["_skills_extra"]:
            print(f"    skills missing: {res['_skills_missing']}  extra: {res['_skills_extra']}")
        time.sleep(DELAY_SECONDS)

    if not results:
        print("No results.")
        return

    k = len(results)
    print(f"\n=== Average over {k} resumes ===")
    for field in ("name", "email", "phone"):
        print(f"{field} exact match: {sum(r[field] for r in results) / k:.2f}")
    for field in ("skills_f1", "projects_f1", "experience_f1", "education_f1"):
        print(f"{field}: {sum(r[field] for r in results) / k:.2f}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    main(count)