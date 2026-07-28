from io import BytesIO
from types import SimpleNamespace

import inspect
import pytest
from starlette.datastructures import (
    Headers,
    UploadFile,
)

from app.api.routes import recruitment
from app.core.exceptions import (
    UnsupportedFileTypeError,
)
from app.core.file_security import (
    ValidatedCVUpload,
)


def create_upload() -> UploadFile:
    return UploadFile(
        filename="../../Candidate Resume.pdf",
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


def build_validated_upload() -> ValidatedCVUpload:
    return ValidatedCVUpload(
        original_filename=(
            "../../Candidate Resume.pdf"
        ),
        safe_filename=(
            "Candidate_Resume.pdf"
        ),
        storage_filename=(
            "secure-random-name.pdf"
        ),
        extension=".pdf",
        content_type="application/pdf",
        content=b"%PDF-valid",
        size_bytes=10,
    )


def unwrap_handler(handler):
    while hasattr(
        handler,
        "__wrapped__",
    ):
        handler = handler.__wrapped__

    return handler


def build_review_result():
    review = {
        "ats_score": 88.0,
        "job_title": "Data Analyst",
        "candidate_intelligence": {
            "recruiter_score": 91.0,
        },
    }

    built_resume = {
        "header": {
            "name": "Jane Candidate",
            "email": "jane@example.com",
        },
        "target_role": "Data Analyst",
    }

    return (
        "Jane Candidate\n"
        "jane@example.com\n"
        "Python SQL experience",
        review,
        built_resume,
    )


@pytest.mark.asyncio
async def test_shared_resume_gateway_validates_and_extracts(
    monkeypatch,
):
    validated = build_validated_upload()

    calls = {
        "validated": 0,
        "extracted": 0,
    }

    async def fake_validate(upload):
        calls["validated"] += 1
        assert upload.filename.endswith(
            "Resume.pdf"
        )
        return validated

    def fake_extract(
        content,
        extension,
    ):
        calls["extracted"] += 1
        assert content == b"%PDF-valid"
        assert extension == ".pdf"
        return (
            "Jane Candidate\n"
            "jane@example.com\n"
            "Python SQL experience"
        )

    monkeypatch.setattr(
        recruitment,
        "validate_cv_upload",
        fake_validate,
    )

    monkeypatch.setattr(
        recruitment.cv_parser,
        "extract_text",
        fake_extract,
    )

    result_upload, raw_text = (
        await recruitment
        .validate_and_extract_resume(
            create_upload()
        )
    )

    assert calls == {
        "validated": 1,
        "extracted": 1,
    }

    assert result_upload is validated
    assert raw_text.startswith(
        "Jane Candidate"
    )


@pytest.mark.asyncio
async def test_review_resume_uses_secure_gateway(
    monkeypatch,
):
    validated = build_validated_upload()
    review_result = build_review_result()

    async def fake_gateway(file):
        return (
            validated,
            review_result[0],
        )

    def fake_review(
        *,
        raw_text,
        target_keywords,
        job_description,
    ):
        assert raw_text == review_result[0]
        assert target_keywords == (
            "Python, SQL"
        )
        assert job_description == (
            "Analyse financial records."
        )
        return review_result

    monkeypatch.setattr(
        recruitment,
        "validate_and_extract_resume",
        fake_gateway,
    )

    monkeypatch.setattr(
        recruitment,
        "review_resume_from_text",
        fake_review,
    )

    handler = unwrap_handler(
        recruitment.review_resume
    )

    result = await handler(
        request=None,
        response=None,
        file=create_upload(),
        target_keywords="Python, SQL",
        job_description=(
            "Analyse financial records."
        ),
        current_user=SimpleNamespace(),
    )

    assert result["filename"] == (
        "Candidate_Resume.pdf"
    )
    assert result["ats_score"] == 88.0
    assert result["built_resume"] == (
        review_result[2]
    )


@pytest.mark.asyncio
async def test_rewrite_cv_uses_secure_gateway(
    monkeypatch,
):
    validated = build_validated_upload()
    review_result = build_review_result()

    monkeypatch.setattr(
        recruitment,
        "validate_and_extract_resume",
        lambda file: None,
    )

    async def fake_gateway(file):
        return (
            validated,
            review_result[0],
        )

    monkeypatch.setattr(
        recruitment,
        "validate_and_extract_resume",
        fake_gateway,
    )

    monkeypatch.setattr(
        recruitment,
        "review_resume_from_text",
        lambda **kwargs: review_result,
    )

    monkeypatch.setattr(
        recruitment.cv_rewriter,
        "rewrite",
        lambda review: {
            "professional_summary": (
                "Rewritten summary"
            )
        },
    )

    handler = unwrap_handler(
        recruitment.rewrite_cv
    )

    result = await handler(
        request=None,
        response=None,
        file=create_upload(),
        target_keywords=None,
        job_description=None,
        current_user=SimpleNamespace(),
    )

    assert result["filename"] == (
        "Candidate_Resume.pdf"
    )
    assert result["rewrite"] == {
        "professional_summary": (
            "Rewritten summary"
        )
    }


@pytest.mark.asyncio
async def test_build_resume_uses_secure_gateway(
    monkeypatch,
):
    validated = build_validated_upload()
    review_result = build_review_result()

    async def fake_gateway(file):
        return (
            validated,
            review_result[0],
        )

    monkeypatch.setattr(
        recruitment,
        "validate_and_extract_resume",
        fake_gateway,
    )

    monkeypatch.setattr(
        recruitment,
        "build_resume_from_text",
        lambda **kwargs: review_result,
    )

    handler = unwrap_handler(
        recruitment.build_resume
    )

    result = await handler(
        request=None,
        response=None,
        file=create_upload(),
        target_keywords=None,
        job_description=None,
        current_user=SimpleNamespace(),
    )

    assert result["filename"] == (
        "Candidate_Resume.pdf"
    )
    assert result["built_resume"] == (
        review_result[2]
    )


@pytest.mark.asyncio
async def test_download_cv_docx_uses_secure_gateway(
    monkeypatch,
):
    validated = build_validated_upload()
    review_result = build_review_result()

    async def fake_gateway(file):
        return (
            validated,
            review_result[0],
        )

    monkeypatch.setattr(
        recruitment,
        "validate_and_extract_resume",
        fake_gateway,
    )

    monkeypatch.setattr(
        recruitment,
        "build_resume_from_text",
        lambda **kwargs: review_result,
    )

    monkeypatch.setattr(
        recruitment.docx_generator,
        "generate_cv_docx",
        lambda built_resume: BytesIO(
            b"generated-cv"
        ),
    )

    handler = unwrap_handler(
        recruitment.download_cv_docx
    )

    result = await handler(
        request=None,
        response=None,
        file=create_upload(),
        target_keywords=None,
        job_description=None,
        current_user=SimpleNamespace(),
    )

    assert result.media_type == (
        "application/vnd.openxmlformats-"
        "officedocument.wordprocessingml."
        "document"
    )

    assert (
        "Jane_Candidate_Data_Analyst_"
        "Optimized_CV.docx"
        in result.headers[
            "content-disposition"
        ]
    )


@pytest.mark.asyncio
async def test_download_application_pack_uses_secure_gateway(
    monkeypatch,
):
    validated = build_validated_upload()
    review_result = build_review_result()

    async def fake_gateway(file):
        return (
            validated,
            review_result[0],
        )

    monkeypatch.setattr(
        recruitment,
        "validate_and_extract_resume",
        fake_gateway,
    )

    monkeypatch.setattr(
        recruitment,
        "build_resume_from_text",
        lambda **kwargs: review_result,
    )

    monkeypatch.setattr(
        recruitment.docx_generator,
        "generate_application_pack_docx",
        lambda built_resume: BytesIO(
            b"generated-pack"
        ),
    )

    handler = unwrap_handler(
        recruitment
        .download_application_pack_docx
    )

    result = await handler(
        request=None,
        response=None,
        file=create_upload(),
        target_keywords=None,
        job_description=None,
        current_user=SimpleNamespace(),
    )

    assert result.media_type == (
        "application/vnd.openxmlformats-"
        "officedocument.wordprocessingml."
        "document"
    )

    assert (
        "Jane_Candidate_Data_Analyst_"
        "Application_Pack.docx"
        in result.headers[
            "content-disposition"
        ]
    )


@pytest.mark.asyncio
async def test_validation_failure_stops_text_extraction(
    monkeypatch,
):
    extraction_called = False

    async def fake_validate(upload):
        raise UnsupportedFileTypeError(
            "Only PDF and DOCX files are supported."
        )

    def fake_extract(
        content,
        extension,
    ):
        nonlocal extraction_called
        extraction_called = True
        return "should not run"

    monkeypatch.setattr(
        recruitment,
        "validate_cv_upload",
        fake_validate,
    )

    monkeypatch.setattr(
        recruitment.cv_parser,
        "extract_text",
        fake_extract,
    )

    with pytest.raises(
        UnsupportedFileTypeError
    ):
        await recruitment.validate_and_extract_resume(
            create_upload()
        )

    assert extraction_called is False


def test_legacy_upload_helpers_are_removed():
    source = inspect.getsource(
        recruitment
    )

    assert not hasattr(
        recruitment,
        "validate_resume_file",
    )

    assert not hasattr(
        recruitment,
        "extract_text_from_upload",
    )

    assert "await file.read()" not in source
    assert "SUPPORTED_RESUME_EXTENSIONS" not in source
    assert "from io import BytesIO" not in source
    assert "from docx import Document" not in source
    assert "from pypdf import PdfReader" not in source