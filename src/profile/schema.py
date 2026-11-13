"""Candidate profile schema for ACCA.

This is the single structured format that every agent will read from.
Keep it stable: changing it later affects parsing, DB and all agents.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class Education(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    score: Optional[str] = None  # CGPA / percentage as written in the resume


class Experience(BaseModel):
    role: str
    organization: str
    duration: Optional[str] = None
    description: Optional[str] = None


class Project(BaseModel):
    title: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class Skills(BaseModel):
    technical: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    education: List[Education] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)