# src/matching/agent.py
from concurrent.futures import ThreadPoolExecutor

from src.matching.retrieve import retrieve_for_profile
from src.matching.score import MatchResult, score_job
from src.profile.schema import CandidateProfile


def _safe_score(profile: CandidateProfile, job: dict) -> dict | None:
    try:
        result: MatchResult = score_job(profile, job)
        return {"job": job, "match": result}
    except RuntimeError as e:
        print(f"   skipped {job['job_id']}: {e}")
        return None


def match_profile(profile: CandidateProfile, k: int = 10, workers: int = 3) -> list[dict]:
    """Retrieve top-k jobs, score them in parallel, return ranked high to low."""
    jobs = retrieve_for_profile(profile, k=k)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda j: _safe_score(profile, j), jobs))
    ranked = [r for r in results if r is not None]
    ranked.sort(key=lambda r: r["match"].score, reverse=True)
    return ranked