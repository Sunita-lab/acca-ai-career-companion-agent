# src/matching/agent.py
import time

from src.matching.retrieve import retrieve_for_profile
from src.matching.score import MatchResult, score_job
from src.profile.schema import CandidateProfile


def match_profile(profile: CandidateProfile, k: int = 10, pause: float = 3.0) -> list[dict]:
    """Retrieve top-k jobs, score each with the LLM, return ranked high to low."""
    ranked = []
    for job in retrieve_for_profile(profile, k=k):
        try:
            result: MatchResult = score_job(profile, job)
        except RuntimeError as e:
            print(f"   skipped {job['job_id']}: {e}")
            continue
        ranked.append({"job": job, "match": result})
        time.sleep(pause)  # free-tier rate limit
    ranked.sort(key=lambda r: r["match"].score, reverse=True)
    return ranked