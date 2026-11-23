# src/matching/retrieve.py
import json
from pathlib import Path

from src.profile.schema import CandidateProfile
from src.rag.search import search_jobs

JOBS_PATH = Path("data/jobs/jobs_clean.json")


def load_jobs() -> dict[str, dict]:
    jobs = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    return {j["job_id"]: j for j in jobs}


def profile_to_query(p: CandidateProfile) -> str:
    """Profile ko ek search query text mein badlo."""
    parts = []
    if p.skills.technical:
        parts.append("Skills: " + ", ".join(p.skills.technical))
    if p.projects:
        proj = "; ".join(
            f"{pr.title} ({', '.join(pr.technologies)})" for pr in p.projects
        )
        parts.append("Projects: " + proj)
    if p.experience:
        parts.append("Experience: " + "; ".join(e.role for e in p.experience))
    if p.education:
        parts.append("Education: " + "; ".join(e.degree for e in p.education))
    return "Internship for a student. " + ". ".join(parts)


def retrieve_for_profile(p: CandidateProfile, k: int = 10) -> list[dict]:
    """Top-k jobs: poori job details + retrieval score."""
    all_jobs = load_jobs()
    hits = search_jobs(profile_to_query(p), k=k)
    return [{**all_jobs[h["job_id"]], "retrieval_score": h["score"]} for h in hits]