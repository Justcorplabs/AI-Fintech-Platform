from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(
        from_attributes=True
    )


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

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )


class HumanReviewAuditOut(BaseModel):
    reviewed: bool
    reviewed_by_user_id: Optional[str]
    reviewed_by_email: Optional[str]
    reviewed_at: Optional[datetime]
    decision: Optional[str]
    notes: Optional[str]

    model_config = ConfigDict(
        extra="allow"
    )


class ScoringAuditOut(BaseModel):
    policy_version: str
    calculated_at: datetime
    job_context_available: bool
    components: Dict[str, float]
    weights: Dict[str, float]
    reference_scores: Dict[str, float]
    adjustments: Dict[str, Any]
    calculation: Dict[str, Any]
    matched_requirements: List[str]
    missing_requirements: List[str]
    final_score: float
    recommendation: str
    thresholds: Dict[str, float]
    human_review: HumanReviewAuditOut

    model_config = ConfigDict(
        extra="allow"
    )


class CandidateScoreOut(BaseModel):
    application_id: UUID
    match_score: float
    reasoning: str
    matched_skills: List[str]
    missing_skills: List[str]
    experience_score: float
    skill_score: float
    education_score: float
    scoring_policy_version: Optional[str] = None


class RecruitmentDashboardOut(BaseModel):
    total_jobs: int
    total_applications: int
    parsed_applications: int
    scored_applications: int
    shortlisted: int
    rejected: int