# src/matching/score.py
import json

from pydantic import BaseModel, Field, ValidationError

from src.llm import ask_llm
from src.profile.schema import CandidateProfile


class MatchResult(BaseModel):
    job_id: str
    score: int = Field(..., ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    reasoning: str = Field(..., min_length=20)


SYSTEM = (
    "You are a strict internship-matching evaluator. Compare a student profile "
    "with ONE internship posting. Use only facts present in the profile and the "
    "posting. Return only valid JSON."
)

RUBRIC = """Scoring rubric (total 100):
- Required skills coverage: 50 points (matched required / total required)
- Preferred skills coverage: 10 points
- Relevant projects and experience: 25 points
- Education and experience-level fit: 15 points
Be consistent: the same input must give the same score."""

PROMPT = """{rubric}

STUDENT PROFILE:
{profile}

INTERNSHIP POSTING:
{job}

Return JSON exactly in this shape:
{{"job_id": "{job_id}", "score": <int 0-100>, "matched_skills": [str],
"missing_skills": [str], "reasoning": "<2-3 sentences: why it matches or not>"}}

matched_skills and missing_skills must come from the posting's required and preferred skills."""


def _job_text(job: dict) -> str:
    keys = ["job_id", "title", "company", "location", "description",
            "responsibilities", "required_skills", "preferred_skills",
            "qualifications", "experience_required", "education_required"]
    return json.dumps({k: job.get(k) for k in keys}, ensure_ascii=False, indent=1)


def score_job(profile: CandidateProfile, job: dict, max_retries: int = 3) -> MatchResult:
    prompt = PROMPT.format(
        rubric=RUBRIC,
        profile=profile.model_dump_json(indent=1),
        job=_job_text(job),
        job_id=job["job_id"],
    )
    last_error = ""
    for attempt in range(max_retries):
        full_prompt = prompt
        if last_error:
            full_prompt += f"\n\nYour previous answer was invalid: {last_error}\nFix it and return valid JSON only."
        try:
            raw = ask_llm(full_prompt, system=SYSTEM, json_mode=True, temperature=0.0)
            result = MatchResult(**json.loads(raw))
            if result.job_id != job["job_id"]:
                raise ValueError(f"job_id must be {job['job_id']}")
            return result
        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            last_error = str(e)[:300]
            print(f"   invalid output (try {attempt + 1}/{max_retries}): {last_error}")
    raise RuntimeError(f"Could not get valid match for {job['job_id']}")