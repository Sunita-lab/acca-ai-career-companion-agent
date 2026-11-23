# scripts/test_match.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.profile.schema import CandidateProfile
from src.matching.agent import match_profile

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

for i, r in enumerate(match_profile(profile, k=10), 1):
    j, m = r["job"], r["match"]
    print(f"{i:2d}. {m.score:3d} | {j['job_id']} | {j['title']} | {j['company']} | {j['location']}")