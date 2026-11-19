# src/jobs/schema.py
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class JobPosting(BaseModel):
    job_id: str = Field(..., description="Unique id, e.g. JOB-001")
    title: str
    company: str
    location: str                      # e.g. "Bangalore", "Remote"
    duration: Optional[str] = None     # e.g. "3 months"
    stipend: Optional[str] = None      # e.g. "INR 15000/month"
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    experience_required: Optional[str] = None   # e.g. "0-1 years"
    education_required: Optional[str] = None    # e.g. "B.Tech CS/IT"
    domain: Optional[str] = None        # e.g. "ML/AI", "Web Backend"

    @field_validator("title", "company", "description")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field cannot be empty")
        return v.strip()

    @field_validator("required_skills")
    @classmethod
    def at_least_one_skill(cls, v: List[str]) -> List[str]:
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("required_skills cannot be empty")
        return cleaned