import re
import uuid
from io import BytesIO
from typing import List, Optional

from docx import Document
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pypdf import PdfReader
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.dependencies import require_permission
from app.core.permissions import Permission
from app.core.rate_limit import (
    CANDIDATE_SCORING_LIMIT,
    RESUME_AI_LIMIT,
    authenticated_user_key,
    limiter,
)
from app.db.database import get_db
from app.models.recruitment import (
    ApplicationStatus,
    CVApplication,
    JobPost,
)
from app.models.user import User
from app.schemas.recruitment import (
    CandidateScoreOut,
    CVApplicationOut,
    JobCreate,
    JobOut,
    RecruitmentDashboardOut,
)
from app.services.recruitment.candidate_intelligence import (
    candidate_intelligence,
)
from app.services.recruitment.cv_parser import cv_parser
from app.services.recruitment.cv_rewriter import cv_rewriter
from app.services.recruitment.docx_generator import docx_generator
from app.services.recruitment.resume_builder import resume_builder
from app.services.recruitment.resume_reviewer import resume_reviewer


router = APIRouter(
    prefix="/recruitment",
    tags=["Recruitment & CV Screening"],
)


jobs_read_access = require_permission(
    Permission.JOBS_READ
)

jobs_write_access = require_permission(
    Permission.JOBS_WRITE
)

recruitment_read_access = require_permission(
    Permission.RECRUITMENT_READ
)

recruitment_write_access = require_permission(
    Permission.RECRUITMENT_WRITE
)


SUPPORTED_RESUME_EXTENSIONS = (
    ".pdf",
    ".txt",
    ".docx",
)


def validate_resume_file(
    file: UploadFile,
) -> str:
    filename = file.filename or ""

    if not filename.lower().endswith(
        SUPPORTED_RESUME_EXTENSIONS
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF, TXT, and DOCX "
                "files are accepted."
            ),
        )

    return filename


def extract_text_from_upload(
    filename: str,
    content: bytes,
) -> str:
    name = filename.lower()

    if name.endswith(".txt"):
        return content.decode(
            "utf-8",
            errors="ignore",
        )

    if name.endswith(".pdf"):
        reader = PdfReader(
            BytesIO(content)
        )

        pages = [
            page.extract_text() or ""
            for page in reader.pages
        ]

        return "\n".join(
            pages
        ).strip()

    if name.endswith(".docx"):
        document = Document(
            BytesIO(content)
        )

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        ).strip()

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type.",
    )


def parse_keywords(
    target_keywords: Optional[str],
):
    if not target_keywords:
        return None

    return [
        keyword.strip().lower()
        for keyword in target_keywords.split(",")
        if keyword.strip()
    ]


def safe_filename(
    value: str,
    fallback: str = "sentinel_ai_document",
) -> str:
    name = value or fallback

    name = re.sub(
        r"[^a-zA-Z0-9_\-]+",
        "_",
        name.strip(),
    )

    name = re.sub(
        r"_+",
        "_",
        name,
    ).strip("_")

    return name or fallback


def parse_uuid(
    value: str,
) -> uuid.UUID:
    try:
        return uuid.UUID(value)

    except (
        ValueError,
        AttributeError,
        TypeError,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid ID format.",
        )


def build_job_description_from_job(
    job: JobPost,
) -> str:
    parts = []

    if job.title:
        parts.append(
            str(job.title)
        )

    if job.organisation:
        parts.append(
            f"Organisation: "
            f"{job.organisation}"
        )

    if (
        job.required_experience_years
        is not None
    ):
        parts.append(
            f"Required experience years: "
            f"{job.required_experience_years}"
        )

    if job.required_skills:
        parts.append(
            "Required skills: "
            + ", ".join(
                job.required_skills
            )
        )

    if job.description:
        parts.append(
            str(job.description)
        )

    return "\n\n".join(
        parts
    ).strip()


def review_resume_from_upload(
    file: UploadFile,
    content: bytes,
    target_keywords: Optional[str],
    job_description: Optional[str],
):
    filename = file.filename or "resume"

    raw_text = extract_text_from_upload(
        filename,
        content,
    )

    if (
        not raw_text
        or len(raw_text.strip()) < 20
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not extract readable "
                "text from this resume."
            ),
        )

    review = resume_reviewer.review_resume(
        raw_text=raw_text,
        target_keywords=parse_keywords(
            target_keywords
        ),
        job_description=job_description,
    )

    built_resume = resume_builder.build(
        raw_text,
        review,
    )

    review["candidate_intelligence"] = (
        candidate_intelligence.generate(
            review=review,
            built_resume=built_resume,
        )
    )

    return (
        raw_text,
        review,
        built_resume,
    )


def build_resume_from_upload(
    file: UploadFile,
    content: bytes,
    target_keywords: Optional[str],
    job_description: Optional[str],
):
    return review_resume_from_upload(
        file=file,
        content=content,
        target_keywords=target_keywords,
        job_description=job_description,
    )


def score_candidate_with_sentinel(
    job: JobPost,
    file: UploadFile,
    content: bytes,
):
    job_description = (
        build_job_description_from_job(
            job
        )
    )

    (
        raw_text,
        review,
        built_resume,
    ) = review_resume_from_upload(
        file=file,
        content=content,
        target_keywords=None,
        job_description=job_description,
    )

    intelligence = (
        review.get(
            "candidate_intelligence",
            {},
        )
        or {}
    )

    recruiter_score = float(
        intelligence.get(
            "recruiter_score"
        )
        or 0
    )

    ats_score = float(
        review.get("ats_score")
        or 0
    )

    job_match_score = float(
        review.get("job_match_score")
        or 0
    )

    skill_score = float(
        review.get("skills_score")
        or 0
    )

    education_score = float(
        review.get("education_score")
        or 0
    )

    experience_score = float(
        review.get("experience_score")
        or 0
    )

    matched_skills = (
        review.get(
            "found_keywords",
            [],
        )
        or []
    )

    missing_skills = (
        review.get(
            "missing_keywords",
            [],
        )
        or []
    )

    header = (
        built_resume.get(
            "header",
            {},
        )
        or {}
    )

    candidate_name = header.get(
        "name"
    )

    candidate_email = header.get(
        "email"
    )

    parsed = cv_parser.parse(
        raw_text
    )

    if not candidate_name:
        candidate_name = parsed.get(
            "name"
        )

    if not candidate_email:
        candidate_email = parsed.get(
            "email"
        )

    education_entries = (
        built_resume.get(
            "education",
            [],
        )
        or []
    )

    education_level = (
        education_entries[0]
        if education_entries
        else parsed.get(
            "education_level"
        )
    )

    recommendation = (
        intelligence.get(
            "hiring_recommendation",
            "Review required",
        )
    )

    missing_requirements = (
        ", ".join(
            missing_skills[:8]
        )
        if missing_skills
        else "None"
    )

    reasoning = (
        f"Sentinel AI Recruiter Score: "
        f"{recruiter_score:.2f}%. "
        f"ATS Score: {ats_score:.2f}%. "
        f"Job Match Score: "
        f"{job_match_score:.2f}%. "
        f"Skills Score: "
        f"{skill_score:.2f}%. "
        f"Education Score: "
        f"{education_score:.2f}%. "
        f"Experience Score: "
        f"{experience_score:.2f}%. "
        f"Recommendation: "
        f"{recommendation}. "
        f"Missing requirements: "
        f"{missing_requirements}."
    )

    return {
        "raw_text": raw_text,
        "parsed": parsed,
        "review": review,
        "built_resume": built_resume,
        "candidate_intelligence": (
            intelligence
        ),
        "candidate_name": (
            candidate_name
        ),
        "candidate_email": (
            candidate_email
        ),
        "education_level": (
            education_level
        ),
        "extracted_skills": (
            matched_skills
        ),
        "match_score": round(
            recruiter_score,
            2,
        ),
        "reasoning": reasoning,
        "matched_skills": (
            matched_skills
        ),
        "missing_skills": (
            missing_skills
        ),
        "experience_score": round(
            experience_score,
            2,
        ),
        "skill_score": round(
            skill_score,
            2,
        ),
        "education_score": round(
            education_score,
            2,
        ),
    }


@router.post(
    "/jobs",
    response_model=JobOut,
    status_code=201,
)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        jobs_write_access
    ),
):
    job = JobPost(
        title=payload.title,
        description=payload.description,
        required_skills=(
            payload.required_skills
        ),
        required_experience_years=(
            payload.required_experience_years
        ),
        organisation=(
            payload.organisation
        ),
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get(
    "/jobs",
    response_model=List[JobOut],
)
def get_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        jobs_read_access
    ),
):
    return (
        db.query(JobPost)
        .order_by(
            JobPost.created_at.desc()
        )
        .all()
    )


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        jobs_write_access
    ),
):
    job_uuid = parse_uuid(
        job_id
    )

    job = (
        db.query(JobPost)
        .filter(
            JobPost.id == job_uuid
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    (
        db.query(CVApplication)
        .filter(
            CVApplication.job_post_id
            == job.id
        )
        .delete(
            synchronize_session=False
        )
    )

    db.delete(job)
    db.commit()

    return {
        "message": (
            "Job deleted successfully."
        )
    }


@router.post("/review-resume")
@limiter.limit(
    RESUME_AI_LIMIT,
    key_func=authenticated_user_key,
)
async def review_resume(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    target_keywords: Optional[str] = Form(
        None
    ),
    job_description: Optional[str] = Form(
        None
    ),
    current_user: User = Depends(
        recruitment_read_access
    ),
):
    filename = validate_resume_file(
        file
    )

    content = await file.read()

    (
        _,
        review,
        built_resume,
    ) = review_resume_from_upload(
        file=file,
        content=content,
        target_keywords=target_keywords,
        job_description=job_description,
    )

    return {
        "filename": filename,
        **review,
        "built_resume": built_resume,
    }


@router.post("/rewrite-cv")
@limiter.limit(
    RESUME_AI_LIMIT,
    key_func=authenticated_user_key,
)
async def rewrite_cv(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    target_keywords: Optional[str] = Form(
        None
    ),
    job_description: Optional[str] = Form(
        None
    ),
    current_user: User = Depends(
        recruitment_read_access
    ),
):
    filename = validate_resume_file(
        file
    )

    content = await file.read()

    (
        _,
        review,
        built_resume,
    ) = review_resume_from_upload(
        file=file,
        content=content,
        target_keywords=target_keywords,
        job_description=job_description,
    )

    rewrite = cv_rewriter.rewrite(
        review
    )

    return {
        "filename": filename,
        "review": review,
        "rewrite": rewrite,
        "built_resume": built_resume,
        "candidate_intelligence": (
            review.get(
                "candidate_intelligence"
            )
        ),
    }


@router.post("/build-resume")
@limiter.limit(
    RESUME_AI_LIMIT,
    key_func=authenticated_user_key,
)
async def build_resume(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    target_keywords: Optional[str] = Form(
        None
    ),
    job_description: Optional[str] = Form(
        None
    ),
    current_user: User = Depends(
        recruitment_read_access
    ),
):
    filename = validate_resume_file(
        file
    )

    content = await file.read()

    (
        _,
        review,
        built_resume,
    ) = build_resume_from_upload(
        file=file,
        content=content,
        target_keywords=target_keywords,
        job_description=job_description,
    )

    return {
        "filename": filename,
        "review": review,
        "built_resume": built_resume,
        "candidate_intelligence": (
            review.get(
                "candidate_intelligence"
            )
        ),
    }


@router.post("/download-cv-docx")
@limiter.limit(
    RESUME_AI_LIMIT,
    key_func=authenticated_user_key,
)
async def download_cv_docx(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    target_keywords: Optional[str] = Form(
        None
    ),
    job_description: Optional[str] = Form(
        None
    ),
    current_user: User = Depends(
        recruitment_read_access
    ),
):
    validate_resume_file(
        file
    )

    content = await file.read()

    (
        _,
        review,
        built_resume,
    ) = build_resume_from_upload(
        file=file,
        content=content,
        target_keywords=target_keywords,
        job_description=job_description,
    )

    output = (
        docx_generator.generate_cv_docx(
            built_resume
        )
    )

    candidate_name = (
        built_resume.get(
            "header",
            {},
        ).get("name")
        or "Candidate"
    )

    target_role = (
        built_resume.get(
            "target_role"
        )
        or review.get(
            "job_title"
        )
        or "Optimized_CV"
    )

    filename = (
        safe_filename(
            f"{candidate_name}_"
            f"{target_role}_"
            f"Optimized_CV"
        )
        + ".docx"
    )

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml."
            "document"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="{filename}"'
            )
        },
    )


@router.post(
    "/download-application-pack-docx"
)
@limiter.limit(
    RESUME_AI_LIMIT,
    key_func=authenticated_user_key,
)
async def download_application_pack_docx(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    target_keywords: Optional[str] = Form(
        None
    ),
    job_description: Optional[str] = Form(
        None
    ),
    current_user: User = Depends(
        recruitment_read_access
    ),
):
    validate_resume_file(
        file
    )

    content = await file.read()

    (
        _,
        review,
        built_resume,
    ) = build_resume_from_upload(
        file=file,
        content=content,
        target_keywords=target_keywords,
        job_description=job_description,
    )

    output = (
        docx_generator
        .generate_application_pack_docx(
            built_resume
        )
    )

    candidate_name = (
        built_resume.get(
            "header",
            {},
        ).get("name")
        or "Candidate"
    )

    target_role = (
        built_resume.get(
            "target_role"
        )
        or review.get(
            "job_title"
        )
        or "Application_Pack"
    )

    filename = (
        safe_filename(
            f"{candidate_name}_"
            f"{target_role}_"
            f"Application_Pack"
        )
        + ".docx"
    )

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml."
            "document"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="{filename}"'
            )
        },
    )


@router.post(
    "/upload-cv/{job_id}",
    response_model=CandidateScoreOut,
)
@limiter.limit(
    CANDIDATE_SCORING_LIMIT,
    key_func=authenticated_user_key,
)
async def upload_cv(
    request: Request,
    response: Response,
    job_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        recruitment_write_access
    ),
):
    filename = validate_resume_file(
        file
    )

    job_uuid = parse_uuid(
        job_id
    )

    job = (
        db.query(JobPost)
        .filter(
            JobPost.id == job_uuid
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job post not found.",
        )

    content = await file.read()

    scoring = score_candidate_with_sentinel(
        job=job,
        file=file,
        content=content,
    )

    application = CVApplication(
        job_post_id=job_uuid,
        cv_filename=filename,
        raw_text=scoring["raw_text"],
        candidate_name=(
            scoring["candidate_name"]
        ),
        candidate_email=(
            scoring["candidate_email"]
        ),
        extracted_skills=(
            scoring["extracted_skills"]
        ),
        experience_years=(
            scoring["parsed"].get(
                "experience_years"
            )
        ),
        education_level=(
            scoring["education_level"]
        ),
        parsed_data={
            "legacy_parser": (
                scoring["parsed"]
            ),
            "sentinel_review": (
                scoring["review"]
            ),
            "built_resume": (
                scoring["built_resume"]
            ),
            "candidate_intelligence": (
                scoring[
                    "candidate_intelligence"
                ]
            ),
        },
        status=ApplicationStatus.scored,
        match_score=(
            scoring["match_score"]
        ),
        llm_reasoning=(
            scoring["reasoning"]
        ),
        scored_at=func.now(),
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "application_id": (
            application.id
        ),
        "match_score": (
            scoring["match_score"]
        ),
        "reasoning": (
            scoring["reasoning"]
        ),
        "matched_skills": (
            scoring["matched_skills"]
        ),
        "missing_skills": (
            scoring["missing_skills"]
        ),
        "experience_score": (
            scoring["experience_score"]
        ),
        "skill_score": (
            scoring["skill_score"]
        ),
        "education_score": (
            scoring["education_score"]
        ),
    }


@router.get(
    "/applications/{job_id}",
    response_model=List[
        CVApplicationOut
    ],
)
def get_applications(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        recruitment_read_access
    ),
):
    job_uuid = parse_uuid(
        job_id
    )

    return (
        db.query(CVApplication)
        .filter(
            CVApplication.job_post_id
            == job_uuid
        )
        .order_by(
            CVApplication.match_score
            .desc()
            .nullslast()
        )
        .all()
    )


@router.patch(
    "/applications/{application_id}/status",
    response_model=CVApplicationOut,
)
def update_application_status(
    application_id: str,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        recruitment_write_access
    ),
):
    application_uuid = parse_uuid(
        application_id
    )

    application = (
        db.query(CVApplication)
        .filter(
            CVApplication.id
            == application_uuid
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail=(
                "Application not found."
            ),
        )

    allowed_statuses = {
        "uploaded": (
            ApplicationStatus.uploaded
        ),
        "parsed": (
            ApplicationStatus.parsed
        ),
        "scored": (
            ApplicationStatus.scored
        ),
        "shortlisted": (
            ApplicationStatus.shortlisted
        ),
        "rejected": (
            ApplicationStatus.rejected
        ),
    }

    requested_status = (
        status.strip().lower()
    )

    if (
        requested_status
        not in allowed_statuses
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid application status."
            ),
        )

    application.status = (
        allowed_statuses[
            requested_status
        ]
    )

    db.commit()
    db.refresh(application)

    return application


@router.delete(
    "/applications/{application_id}"
)
def delete_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        recruitment_write_access
    ),
):
    application_uuid = parse_uuid(
        application_id
    )

    application = (
        db.query(CVApplication)
        .filter(
            CVApplication.id
            == application_uuid
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail=(
                "Application not found."
            ),
        )

    db.delete(application)
    db.commit()

    return {
        "message": (
            "Application deleted "
            "successfully."
        )
    }


@router.get(
    "/dashboard",
    response_model=RecruitmentDashboardOut,
)
def recruitment_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        recruitment_read_access
    ),
):
    total_jobs = (
        db.query(JobPost).count()
    )

    total_applications = (
        db.query(CVApplication).count()
    )

    parsed_applications = (
        db.query(CVApplication)
        .filter(
            CVApplication.status
            == ApplicationStatus.parsed
        )
        .count()
    )

    scored_applications = (
        db.query(CVApplication)
        .filter(
            CVApplication.status
            == ApplicationStatus.scored
        )
        .count()
    )

    shortlisted = (
        db.query(CVApplication)
        .filter(
            CVApplication.status
            == ApplicationStatus.shortlisted
        )
        .count()
    )

    rejected = (
        db.query(CVApplication)
        .filter(
            CVApplication.status
            == ApplicationStatus.rejected
        )
        .count()
    )

    return {
        "total_jobs": total_jobs,
        "total_applications": (
            total_applications
        ),
        "parsed_applications": (
            parsed_applications
        ),
        "scored_applications": (
            scored_applications
        ),
        "shortlisted": shortlisted,
        "rejected": rejected,
    }