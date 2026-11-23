# scripts/test_score.py
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.profile.schema import CandidateProfile
from src.matching.retrieve import retrieve_for_profile
from src.matching.score import score_job

profile = CandidateProfile(
    name="Test Student",
    education=[{"degree": "B.Tech CSE", "institution": "Test University", "year": "2027"}],
    skills={"technical": ["Python", "Pandas", "scikit-learn", "SQL", "Machine Learning"]},
    projects=[
        {"title": "House Price Predictor",
         "technologies": ["Python", "scikit-learn", "Pandas"]},
        {"title": "Sales Dashboard", "technologies": ["SQL", "Power BI"]},
    ],
)

for job in retrieve_for_profile(profile, k=3):
    r = score_job(profile, job)
    print(f"\n{r.score:3d} | {job['job_id']} | {job['title']} | {job['company']}")
    print("  matched:", r.matched_skills)
    print("  missing:", r.missing_skills)
    print("  why:", r.reasoning)
    time.sleep(3)