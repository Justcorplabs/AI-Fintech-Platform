from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from starlette.datastructures import (
    Headers,
    UploadFile,
)

from app.api.routes import recruitment
from app.core.exceptions import (
    ResourceNotFoundError,
)
from app.core.file_security import (
    ValidatedCVUpload,
)
from app.models.recruitment import (
    ApplicationStatus,
)
from app.schemas.recruitment import (
    ScoringAuditOut,
)
from app.services.recruitment.scoring_audit import (
    JOB_CONTEXT_WEIGHTS,
    PROFILE_WEIGHTS,
    SCORING_POLICY_VERSION,
    scoring_audit_service,
)


class FakeQuery:
    def __init__(
        self,
        result,
    ):
        self.result = result

    def filter(
        self,
        *args,
        **kwargs,
    ):
        return self

    def first(
        self,
    ):
        return self.result


class FakeSession:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.added = None
        self.committed = False
        self.refreshed = False
        self.rolled_back = False

    def query(
        self,
        model,
    ):
        return FakeQuery(
            self.result
        )

    def add(
        self,
        instance,
    ):
        self.added = instance

    def commit(
        self,
    ):
        self.committed = True

    def refresh(
        self,
        instance,
    ):
        self.refreshed = True

        if getattr(
            instance,
            "id",
            None,
        ) is None:
            instance.id = uuid4()

    def rollback(
        self,
    ):
        self.rolled_back = True


def build_review(
    *,
    job_context_available: bool = True,
):
    return {
        "ats_score": 76.0,
        "job_match_score": 82.0,
        "skills_score": 78.0,
        "education_score": 70.0,
        "experience_score": 74.0,
        "achievement_score": 62.0,
        "formatting_score": 80.0,
        "contact_score": 100.0,
        "scoring_context": {
            "job_context_available": (
                job_context_available
            ),
        },
    }


def build_intelligence(
    *,
    job_context_available: bool = True,
):
    components = (
        {
            "job_match": 82.0,
            "experience": 74.0,
            "education": 70.0,
            "achievements": 62.0,
            "formatting": 80.0,
            "contact": 100.0,
        }
        if job_context_available
        else {
            "skills": 78.0,
            "experience": 74.0,
            "education": 70.0,
            "achievements": 62.0,
            "formatting": 80.0,
            "contact": 100.0,
        }
    )

    return {
        "recruiter_score": 76.0,
        "hiring_recommendation": (
            "Consider After Targeted CV Improvements"
            if job_context_available
            else (
                "Strong Profile — Add a Job "
                "Description for Interview Matching"
            )
        ),
        "score_components": components,
        "scoring_context": {
            "job_context_available": (
                job_context_available
            ),
            "aggregate_ats_used_as_score_input": (
                False
            ),
        },
    }


def build_snapshot():
    return scoring_audit_service.build_snapshot(
        review=build_review(),
        intelligence=build_intelligence(),
        matched_requirements=[
            "Python",
            "SQL",
        ],
        missing_requirements=[
            "Docker",
        ],
        calculated_at=datetime(
            2026,
            7,
            28,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


def create_upload() -> UploadFile:
    return UploadFile(
        filename="Candidate.pdf",
        file=BytesIO(
            b"candidate upload"
        ),
        headers=Headers(
            {
                "content-type": (
                    "application/pdf"
                ),
            }
        ),
    )


def get_upload_handler():
    handler = recruitment.upload_cv

    while hasattr(
        handler,
        "__wrapped__",
    ):
        handler = handler.__wrapped__

    return handler


def build_scoring_result(
    raw_text: str,
):
    review = build_review()
    intelligence = build_intelligence()

    return {
        "raw_text": raw_text,
        "parsed": {
            "name": "Jane Candidate",
            "email": "jane@example.com",
            "experience_years": 3.0,
            "education_level": "Bachelors",
        },
        "review": review,
        "built_resume": {
            "header": {
                "name": "Jane Candidate",
                "email": "jane@example.com",
            },
            "education": [
                "Bachelor of Science",
            ],
        },
        "candidate_intelligence": (
            intelligence
        ),
        "candidate_name": (
            "Jane Candidate"
        ),
        "candidate_email": (
            "jane@example.com"
        ),
        "education_level": (
            "Bachelor of Science"
        ),
        "extracted_skills": [
            "Python",
            "SQL",
        ],
        "match_score": 76.0,
        "reasoning": (
            "Candidate scoring completed."
        ),
        "matched_skills": [
            "Python",
            "SQL",
        ],
        "missing_skills": [
            "Docker",
        ],
        "experience_score": 74.0,
        "skill_score": 78.0,
        "education_score": 70.0,
    }


def test_job_context_snapshot_records_policy():
    snapshot = build_snapshot()

    assert (
        snapshot["policy_version"]
        == SCORING_POLICY_VERSION
    )
    assert (
        snapshot["weights"]
        == JOB_CONTEXT_WEIGHTS
    )
    assert (
        sum(
            snapshot["weights"].values()
        )
        == pytest.approx(1.0)
    )
    assert (
        snapshot["adjustments"][
            "aggregate_ats_used_as_score_input"
        ]
        is False
    )
    assert (
        snapshot["final_score"]
        == 76.0
    )
    assert (
        snapshot["human_review"][
            "reviewed"
        ]
        is False
    )
    assert (
        snapshot["calculation"][
            "weighted_component_total"
        ]
        == 76.0
    )
    assert (
        snapshot["calculation"][
            "final_score_matches_weighted_total"
        ]
        is True
    )

    parsed = ScoringAuditOut.model_validate(
        snapshot
    )

    assert (
        parsed.policy_version
        == SCORING_POLICY_VERSION
    )


def test_profile_snapshot_records_profile_policy():
    snapshot = (
        scoring_audit_service.build_snapshot(
            review=build_review(
                job_context_available=False
            ),
            intelligence=build_intelligence(
                job_context_available=False
            ),
        )
    )

    assert (
        snapshot["job_context_available"]
        is False
    )
    assert (
        snapshot["weights"]
        == PROFILE_WEIGHTS
    )
    assert "skills" in snapshot[
        "components"
    ]
    assert "job_match" not in snapshot[
        "components"
    ]


def test_snapshot_clamps_and_deduplicates():
    review = build_review()
    intelligence = build_intelligence()

    intelligence[
        "recruiter_score"
    ] = 150
    intelligence[
        "score_components"
    ][
        "job_match"
    ] = -5

    snapshot = (
        scoring_audit_service.build_snapshot(
            review=review,
            intelligence=intelligence,
            matched_requirements=[
                " Python ",
                "python",
                "SQL",
                "",
            ],
            missing_requirements=[
                "Docker",
                " docker ",
            ],
        )
    )

    assert snapshot["final_score"] == 100.0
    assert (
        snapshot["components"][
            "job_match"
        ]
        == 0.0
    )
    assert snapshot[
        "matched_requirements"
    ] == [
        "Python",
        "SQL",
    ]
    assert snapshot[
        "missing_requirements"
    ] == [
        "Docker",
    ]


def test_extract_snapshot_returns_copy():
    snapshot = build_snapshot()

    parsed_data = {
        "scoring_audit": snapshot,
    }

    extracted = (
        scoring_audit_service.extract_snapshot(
            parsed_data
        )
    )

    assert extracted == snapshot

    extracted["final_score"] = 1.0

    assert (
        parsed_data["scoring_audit"][
            "final_score"
        ]
        == 76.0
    )


def test_record_human_review_preserves_score():
    snapshot = build_snapshot()
    parsed_data = {
        "scoring_audit": snapshot,
        "legacy_parser": {
            "name": "Jane Candidate",
        },
    }

    reviewer_id = uuid4()

    updated = (
        scoring_audit_service.record_human_review(
            parsed_data=parsed_data,
            reviewer_id=reviewer_id,
            reviewer_email=(
                "RECRUITER@EXAMPLE.COM"
            ),
            decision="shortlisted",
            notes="Evidence verified.",
            reviewed_at=datetime(
                2026,
                7,
                28,
                15,
                30,
                tzinfo=timezone.utc,
            ),
        )
    )

    audit = updated[
        "scoring_audit"
    ]

    assert audit["final_score"] == 76.0
    assert audit["human_review"][
        "reviewed"
    ] is True
    assert audit["human_review"][
        "reviewed_by_user_id"
    ] == str(reviewer_id)
    assert audit["human_review"][
        "reviewed_by_email"
    ] == "recruiter@example.com"
    assert audit["human_review"][
        "decision"
    ] == "shortlisted"

    assert parsed_data[
        "scoring_audit"
    ][
        "human_review"
    ][
        "reviewed"
    ] is False


@pytest.mark.asyncio
async def test_upload_persists_scoring_audit(
    monkeypatch,
):
    job_id = uuid4()

    job = SimpleNamespace(
        id=job_id,
        title="Data Analyst",
        organisation="JustCorp",
        required_experience_years=2,
        required_skills=[
            "Python",
            "SQL",
        ],
        description="Analyse data.",
    )

    db = FakeSession(
        job
    )

    async def fake_validate(
        upload,
    ):
        return ValidatedCVUpload(
            original_filename=(
                "Candidate.pdf"
            ),
            safe_filename=(
                "Candidate.pdf"
            ),
            storage_filename=(
                "storage.pdf"
            ),
            extension=".pdf",
            content_type=(
                "application/pdf"
            ),
            content=b"%PDF-valid",
            size_bytes=10,
        )

    def fake_extract_text(
        content,
        extension,
    ):
        return (
            "Jane Candidate\n"
            "jane@example.com\n"
            "Python SQL"
        )

    def fake_score(
        *,
        job,
        raw_text,
    ):
        return build_scoring_result(
            raw_text
        )

    monkeypatch.setattr(
        recruitment,
        "validate_cv_upload",
        fake_validate,
    )
    monkeypatch.setattr(
        recruitment.cv_parser,
        "extract_text",
        fake_extract_text,
    )
    monkeypatch.setattr(
        recruitment,
        "score_candidate_with_sentinel",
        fake_score,
    )

    handler = get_upload_handler()

    result = await handler(
        request=SimpleNamespace(),
        response=SimpleNamespace(),
        job_id=str(job_id),
        file=create_upload(),
        db=db,
        current_user=SimpleNamespace(
            id=uuid4(),
            email="recruiter@example.com",
        ),
    )

    audit = db.added.parsed_data[
        "scoring_audit"
    ]

    assert (
        audit["policy_version"]
        == SCORING_POLICY_VERSION
    )
    assert (
        audit["final_score"]
        == 76.0
    )
    assert (
        result[
            "scoring_policy_version"
        ]
        == SCORING_POLICY_VERSION
    )


def test_scoring_audit_endpoint_returns_snapshot():
    application_id = uuid4()
    snapshot = build_snapshot()

    application = SimpleNamespace(
        id=application_id,
        parsed_data={
            "scoring_audit": snapshot,
        },
    )

    result = (
        recruitment
        .get_application_scoring_audit(
            application_id=str(
                application_id
            ),
            db=FakeSession(
                application
            ),
            current_user=SimpleNamespace(),
        )
    )

    assert result == snapshot


def test_scoring_audit_endpoint_rejects_missing_application():
    with pytest.raises(
        ResourceNotFoundError,
        match="Application not found",
    ):
        (
            recruitment
            .get_application_scoring_audit(
                application_id=str(
                    uuid4()
                ),
                db=FakeSession(
                    None
                ),
                current_user=SimpleNamespace(),
            )
        )


def test_scoring_audit_endpoint_rejects_legacy_application():
    application = SimpleNamespace(
        id=uuid4(),
        parsed_data={
            "legacy_parser": {},
        },
    )

    with pytest.raises(
        ResourceNotFoundError,
        match="Scoring audit is not available",
    ):
        (
            recruitment
            .get_application_scoring_audit(
                application_id=str(
                    application.id
                ),
                db=FakeSession(
                    application
                ),
                current_user=SimpleNamespace(),
            )
        )


def test_shortlist_records_human_review():
    application_id = uuid4()

    application = SimpleNamespace(
        id=application_id,
        status=ApplicationStatus.scored,
        parsed_data={
            "scoring_audit": (
                build_snapshot()
            ),
        },
    )

    db = FakeSession(
        application
    )

    reviewer_id = uuid4()

    result = (
        recruitment.update_application_status(
            application_id=str(
                application_id
            ),
            status="shortlisted",
            db=db,
            current_user=SimpleNamespace(
                id=reviewer_id,
                email=(
                    "recruiter@example.com"
                ),
            ),
        )
    )

    human_review = result.parsed_data[
        "scoring_audit"
    ][
        "human_review"
    ]

    assert (
        result.status
        == ApplicationStatus.shortlisted
    )
    assert human_review["reviewed"] is True
    assert (
        human_review[
            "reviewed_by_user_id"
        ]
        == str(reviewer_id)
    )
    assert (
        human_review[
            "decision"
        ]
        == "shortlisted"
    )
    assert db.committed is True
    assert db.refreshed is True