"""Resume text -> validated CandidateProfile (LLM + Pydantic + retry)."""
import json

from pydantic import ValidationError

from src.llm import ask_llm
from src.profile.schema import CandidateProfile

SYSTEM = (
    "You extract structured data from resumes. "
    "Return ONLY valid JSON. Use only information present in the resume. "
    "If a field is missing, use null or an empty list. Never invent data."
)

PROMPT_TEMPLATE = """Extract the candidate profile from this resume text.

Return JSON with exactly this structure:
{{
  "name": str,
  "email": str | null,
  "phone": str | null,
  "education": [{{"degree": str, "institution": str, "year": str | null, "score": str | null}}],
  "skills": {{"technical": [str], "soft": [str]}},
  "experience": [{{"role": str, "organization": str, "duration": str | null, "description": str | null}}],
  "projects": [{{"title": str, "description": str | null, "technologies": [str]}}],
  "certifications": [str]
}}

Resume text may come from a multi-column PDF, so lines can be mixed. Use context to separate sections.

RESUME TEXT:
{resume_text}
"""

MAX_ATTEMPTS = 3


def parse_resume(resume_text: str) -> CandidateProfile:
    """Ask the LLM for JSON, validate with Pydantic, retry with error feedback."""
    prompt = PROMPT_TEMPLATE.format(resume_text=resume_text)
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = ask_llm(prompt, system=SYSTEM, json_mode=True)
        try:
            return CandidateProfile.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            prompt = (
                PROMPT_TEMPLATE.format(resume_text=resume_text)
                + f"\n\nYour previous answer was invalid: {e}\n"
                "Fix it and return ONLY valid JSON in the exact structure above."
            )
    raise ValueError(f"Parsing failed after {MAX_ATTEMPTS} attempts: {last_error}")