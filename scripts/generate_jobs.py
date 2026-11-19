# scripts/generate_jobs.py
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import ValidationError
from src.llm import ask_llm
from src.jobs.schema import JobPosting

OUT_PATH = Path("data/jobs/jobs_raw.json")

DOMAINS = [
    "ML/AI", "Data Science", "Data Analytics", "Web Frontend",
    "Web Backend", "Full Stack", "Mobile App", "DevOps/Cloud",
    "Cybersecurity", "UI/UX Design", "QA/Testing", "Product/Business Analyst",
]

SYSTEM = (
    "You generate realistic but entirely SYNTHETIC internship postings for "
    "Indian students. Use FICTIONAL company names only (never real companies). "
    "Return only valid JSON."
)

PROMPT = """Generate {n} different internship postings for the domain: {domain}.

Rules:
- Vary company (fictional), city (Bangalore, Hyderabad, Pune, Delhi NCR, Mumbai, Chennai, Bhubaneswar, Remote), duration (2-6 months), stipend (INR 5000-30000/month) and difficulty.
- Vary the exact role title and the tech stack across postings.
- Do NOT reuse these titles/companies already generated: {used}
- required_skills: 3-6 specific skills. preferred_skills: 2-4 skills.
- responsibilities: 3-5 short bullets. qualifications: 1-3 bullets.
- experience_required like "0-1 years" or "Fresher". education_required like "B.Tech CS/IT or related".
- description: 2-3 sentences.

Return JSON: {{"postings": [{{"title": str, "company": str, "location": str,
"duration": str, "stipend": str, "description": str, "responsibilities": [str],
"required_skills": [str], "preferred_skills": [str], "qualifications": [str],
"experience_required": str, "education_required": str}}]}}"""


def load_existing() -> list[dict]:
    if OUT_PATH.exists():
        return json.loads(OUT_PATH.read_text(encoding="utf-8"))
    return []


def save(jobs: list[dict]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")


def generate_batch(domain: str, n: int, used: list[str]) -> list[dict]:
    prompt = PROMPT.format(n=n, domain=domain, used="; ".join(used[-30:]) or "none")
    for attempt in range(3):
        try:
            raw = ask_llm(prompt, system=SYSTEM, json_mode=True, temperature=0.9)
            return json.loads(raw)["postings"]
        except Exception as e:  # noqa: BLE001
            print(f"   batch parse/call failed (try {attempt + 1}/3): {e}")
    return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-domain", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=5)
    ap.add_argument("--max-domains", type=int, default=len(DOMAINS), help="use 1 for a quick test")
    args = ap.parse_args()

    jobs = load_existing()
    next_id = len(jobs) + 1
    print(f"Existing postings: {len(jobs)}")

    for domain in DOMAINS[: args.max_domains]:
        have = [j for j in jobs if j.get("domain") == domain]
        used = [f"{j['title']} @ {j['company']}" for j in have]
        stalls = 0
        while len(have) < args.per_domain and stalls < 3:
            n = min(args.batch_size, args.per_domain - len(have))
            print(f"[{domain}] have {len(have)}/{args.per_domain}, asking {n} more...")
            added = 0
            for item in generate_batch(domain, n, used):
                item["job_id"] = f"JOB-{next_id:03d}"
                item["domain"] = domain
                try:
                    job = JobPosting(**item)
                except ValidationError as e:
                    print(f"   skipped invalid posting: {e.errors()[0]['msg']}")
                    continue
                jobs.append(job.model_dump())
                have.append(job.model_dump())
                used.append(f"{job.title} @ {job.company}")
                next_id += 1
                added += 1
            stalls = stalls + 1 if added == 0 else 0
            save(jobs)  # save after every batch, so progress is never lost

    print(f"Done. Total postings: {len(jobs)} -> {OUT_PATH}")


if __name__ == "__main__":
    main()