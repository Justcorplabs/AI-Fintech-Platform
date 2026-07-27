from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
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


class FakeQuery:
    def __init__(
        self,
        job,
    ):
        self.job = job

    def filter(
        self,
        *args,
        **kwargs,
    ):
        return self

    def first(
        self,
    ):
        return self.job


class FakeSession:
    def __init__(
        self,
        job,
        *,
        fail_commit: bool = False,
    ):
        self.job = job
        self.fail_commit = fail_commit
        self.added = None
        self.committed = False
        self.rolled_back = False

    def query(
        self,
        model,
    ):
        return FakeQuery(
            self.job
        )

    def add(
        self,
        instance,
    ):
        self.added = instance

    def commit(
        self,
    ):
        if self.fail_commit:
            raise SQLAlchemyError(
                "Test database failure"
            )

        self.committed = True

    def refresh(
        self,
        instance,
    ):
        if instance.id is None:
            instance.id = uuid4()

    def rollback(
        self,
    ):
        self.rolled_back = True


def create_upload() -> UploadFile:
    return UploadFile(
        filename="../../Candidate CV.pdf",
        file=BytesIO(
            b"untrusted upload bytes"
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
    return {
        "raw_text": raw_text,
        "parsed": {
            "name": "Jane Candidate",
            "email": "jane@example.com",
            "phone": "+263771234567",
            "education_level": "Bachelors",
            "experience_years": 3.0,
            "extracted_skills": [
                "python",
                "sql",
            ],
        },
        "review": {
            "ats_score": 88.0,
        },
        "built_resume": {
            "header": {
                "name": "Jane Candidate",
                "email": "jane@example.com",
            },
        },
        "candidate_intelligence": {
            "recruiter_score": 91.0,
        },
        "candidate_name": (
            "Jane Candidate"
        ),
        "candidate_email": (
            "jane@example.com"
        ),
        "education_level": (
            "Bachelors"
        ),
        "extracted_skills": [
            "python",
            "sql",
        ],
        "match_score": 91.0,
        "reasoning": (
            "Candidate matches the role."
        ),
        "matched_skills": [
            "python",
            "sql",
        ],
        "missing_skills": [
            "docker",
        ],
        "experience_score": 85.0,
        "skill_score": 90.0,
        "education_score": 80.0,
    }


@pytest.mark.asyncio
async def test_upload_cv_uses_secure_validation(
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
        description="Analyse financial data.",
    )

    db = FakeSession(
        job
    )

    calls = {
        "validated": 0,
        "extracted": 0,
        "scored": 0,
    }

    async def fake_validate(
        upload,
    ):
        calls["validated"] += 1

        return ValidatedCVUpload(
            original_filename=(
                "../../Candidate CV.pdf"
            ),
            safe_filename=(
                "Candidate_CV.pdf"
            ),
            storage_filename=(
                "random-storage-name.pdf"
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
        calls["extracted"] += 1

        assert content == b"%PDF-valid"
        assert extension == ".pdf"

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
        calls["scored"] += 1

        assert job.id == job_id

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
        request=None,
        response=None,
        job_id=str(job_id),
        file=create_upload(),
        db=db,
        current_user=SimpleNamespace(
            id=uuid4()
        ),
    )

    assert calls == {
        "validated": 1,
        "extracted": 1,
        "scored": 1,
    }

    assert db.committed is True
    assert db.rolled_back is False
    assert db.added is not None

    assert db.added.cv_filename == (
        "Candidate_CV.pdf"
    )

    assert db.added.raw_text.startswith(
        "Jane Candidate"
    )

    upload_metadata = (
        db.added.parsed_data[
            "upload_security"
        ]
    )

    assert upload_metadata == {
        "original_filename": (
            "../../Candidate CV.pdf"
        ),
        "safe_filename": (
            "Candidate_CV.pdf"
        ),
        "extension": ".pdf",
        "content_type": (
            "application/pdf"
        ),
        "size_bytes": 10,
    }

    assert result[
        "application_id"
    ] == db.added.id

    assert result[
        "match_score"
    ] == 91.0


@pytest.mark.asyncio
async def test_upload_cv_validates_job_before_file(
    monkeypatch,
):
    db = FakeSession(
        None
    )

    validator_called = False

    async def fake_validate(
        upload,
    ):
        nonlocal validator_called
        validator_called = True

    monkeypatch.setattr(
        recruitment,
        "validate_cv_upload",
        fake_validate,
    )

    handler = get_upload_handler()

    with pytest.raises(
        ResourceNotFoundError
    ):
        await handler(
            request=None,
            response=None,
            job_id=str(uuid4()),
            file=create_upload(),
            db=db,
            current_user=SimpleNamespace(
                id=uuid4()
            ),
        )

    assert validator_called is False
    assert db.added is None


@pytest.mark.asyncio
async def test_upload_cv_rolls_back_database_error(
    monkeypatch,
):
    job_id = uuid4()

    job = SimpleNamespace(
        id=job_id,
    )

    db = FakeSession(
        job,
        fail_commit=True,
    )

    async def fake_validate(
        upload,
    ):
        return ValidatedCVUpload(
            original_filename=(
                "candidate.pdf"
            ),
            safe_filename=(
                "candidate.pdf"
            ),
            storage_filename=(
                "random.pdf"
            ),
            extension=".pdf",
            content_type=(
                "application/pdf"
            ),
            content=b"%PDF-valid",
            size_bytes=10,
        )

    monkeypatch.setattr(
        recruitment,
        "validate_cv_upload",
        fake_validate,
    )

    monkeypatch.setattr(
        recruitment.cv_parser,
        "extract_text",
        lambda content, extension: (
            "Jane Candidate\n"
            "jane@example.com\n"
            "Python SQL"
        ),
    )

    monkeypatch.setattr(
        recruitment,
        "score_candidate_with_sentinel",
        lambda **kwargs: (
            build_scoring_result(
                kwargs["raw_text"]
            )
        ),
    )

    handler = get_upload_handler()

    with pytest.raises(
        SQLAlchemyError
    ):
        await handler(
            request=None,
            response=None,
            job_id=str(job_id),
            file=create_upload(),
            db=db,
            current_user=SimpleNamespace(
                id=uuid4()
            ),
        )

    assert db.rolled_back is True