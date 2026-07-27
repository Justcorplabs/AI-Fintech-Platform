from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    required_experience_years: int = 0
    organisation: str = ""


class JobOut(BaseModel):
    id: UUID
    title: str
    description: str
    required_skills: List[str]
    required_experience_years: int
    organisation: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CVApplicationOut(BaseModel):
    id: UUID
    candidate_name: Optional[str]
    candidate_email: Optional[str]
    cv_filename: Optional[str]
    extracted_skills: List[str]
    experience_years: Optional[float]
    education_level: Optional[str]
    match_score: Optional[float]
    llm_reasoning: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class CandidateScoreOut(BaseModel):
    application_id: UUID
    match_score: float
    reasoning: str
    matched_skills: List[str]
    missing_skills: List[str]
    experience_score: float
    skill_score: float
    education_score: float


class RecruitmentDashboardOut(BaseModel):
    total_jobs: int
    total_applications: int
    parsed_applications: int
    scored_applications: int
    shortlisted: int
    rejected: int