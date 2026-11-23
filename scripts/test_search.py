# scripts/test_search.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rag.search import search_jobs

QUERIES = [
    "machine learning internship with Python and PyTorch",
    "frontend React internship in Bangalore",
    "remote data analytics internship with SQL and Power BI",
    "cybersecurity internship penetration testing",
    "UI UX design internship with Figma",
]

for q in QUERIES:
    print(f"\nQUERY: {q}")
    for r in search_jobs(q, k=5):
        print(f"  {r['score']:.3f} | {r['job_id']} | {r['title']} | {r['company']} | {r['location']} | {r['domain']}")