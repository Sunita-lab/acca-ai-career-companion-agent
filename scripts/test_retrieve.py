# scripts/test_retrieve.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.profile.schema import CandidateProfile
from src.matching.retrieve import profile_to_query, retrieve_for_profile

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

print("QUERY:", profile_to_query(profile), "\n")
for j in retrieve_for_profile(profile, k=10):
    print(f"{j['retrieval_score']:.3f} | {j['job_id']} | {j['title']} | {j['company']} | {j['domain']}")