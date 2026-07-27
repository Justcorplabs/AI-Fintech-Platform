from sqlalchemy import Column, String, Float, DateTime, Text, Integer, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid
import enum

from app.db.database import Base


class ApplicationStatus(str, enum.Enum):
    uploaded = "uploaded"
    parsed = "parsed"
    scored = "scored"
    shortlisted = "shortlisted"
    rejected = "rejected"


class JobPost(Base):
    __tablename__ = "job_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(ARRAY(String), default=[])
    required_experience_years = Column(Integer, default=0)
    organisation = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CVApplication(Base):
    __tablename__ = "cv_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_post_id = Column(UUID(as_uuid=True), nullable=False)
    candidate_name = Column(String)
    candidate_email = Column(String)
    cv_filename = Column(String)
    raw_text = Column(Text, nullable=True)

    extracted_skills = Column(ARRAY(String), default=[])
    experience_years = Column(Float, nullable=True)
    education_level = Column(String, nullable=True)
    parsed_data = Column(JSONB, nullable=True)

    match_score = Column(Float, nullable=True)
    llm_reasoning = Column(Text, nullable=True)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.uploaded)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    scored_at = Column(DateTime(timezone=True), nullable=True)