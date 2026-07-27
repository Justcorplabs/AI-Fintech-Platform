from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfWriter
from starlette.datastructures import (
    Headers,
    UploadFile,
)

from app.core.exceptions import (
    BadRequestError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.core.file_security import (
    sanitize_filename,
    validate_cv_upload,
)


def create_upload(
    *,
    filename: str,
    content: bytes,
    content_type: str,
) -> UploadFile:
    """
    Create an in-memory UploadFile for security tests.
    """

    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers=Headers(
            {
                "content-type": content_type,
            }
        ),
    )


def create_docx_bytes() -> bytes:
    """
    Create a valid DOCX document in memory.
    """

    document = Document()

    document.add_paragraph(
        "Test Candidate"
    )

    stream = BytesIO()

    document.save(stream)

    return stream.getvalue()


def create_pdf_bytes() -> bytes:
    """
    Create a valid PDF document in memory.
    """

    writer = PdfWriter()

    writer.add_blank_page(
        width=612,
        height=792,
    )

    stream = BytesIO()

    writer.write(stream)

    return stream.getvalue()


def test_filename_is_sanitized():
    result = sanitize_filename(
        "../../unsafe candidate?.pdf"
    )

    assert result == (
        "unsafe_candidate.pdf"
    )


def test_windows_path_traversal_is_removed():
    result = sanitize_filename(
        r"..\..\candidate cv.docx"
    )

    assert result == (
        "candidate_cv.docx"
    )


def test_empty_filename_is_safely_normalized():
    result = sanitize_filename(
        ".pdf"
    )

    assert result == "cv.pdf"


@pytest.mark.asyncio
async def test_valid_docx_is_accepted():
    docx_content = create_docx_bytes()

    upload = create_upload(
        filename="candidate.docx",
        content=docx_content,
        content_type=(
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml.document"
        ),
    )

    validated = await validate_cv_upload(
        upload
    )

    assert validated.extension == ".docx"

    assert validated.size_bytes == len(
        docx_content
    )

    assert validated.safe_filename == (
        "candidate.docx"
    )

    assert validated.storage_filename.endswith(
        ".docx"
    )

    assert validated.content == docx_content


@pytest.mark.asyncio
async def test_valid_pdf_is_accepted():
    pdf_content = create_pdf_bytes()

    upload = create_upload(
        filename="candidate.pdf",
        content=pdf_content,
        content_type="application/pdf",
    )

    validated = await validate_cv_upload(
        upload
    )

    assert validated.extension == ".pdf"

    assert validated.content.startswith(
        b"%PDF-"
    )

    assert validated.content == pdf_content

    assert validated.storage_filename.endswith(
        ".pdf"
    )


@pytest.mark.asyncio
async def test_generic_mime_type_is_allowed_when_signature_is_valid():
    upload = create_upload(
        filename="candidate.pdf",
        content=create_pdf_bytes(),
        content_type=(
            "application/octet-stream"
        ),
    )

    validated = await validate_cv_upload(
        upload
    )

    assert validated.extension == ".pdf"


@pytest.mark.asyncio
async def test_empty_file_is_rejected():
    upload = create_upload(
        filename="candidate.pdf",
        content=b"",
        content_type="application/pdf",
    )

    with pytest.raises(
        BadRequestError
    ):
        await validate_cv_upload(
            upload
        )


@pytest.mark.asyncio
async def test_missing_filename_is_rejected():
    upload = create_upload(
        filename="",
        content=create_pdf_bytes(),
        content_type="application/pdf",
    )

    with pytest.raises(
        BadRequestError
    ):
        await validate_cv_upload(
            upload
        )


@pytest.mark.asyncio
async def test_unsupported_extension_is_rejected():
    upload = create_upload(
        filename="candidate.exe",
        content=b"MZ",
        content_type=(
            "application/octet-stream"
        ),
    )

    with pytest.raises(
        UnsupportedFileTypeError
    ):
        await validate_cv_upload(
            upload
        )


@pytest.mark.asyncio
async def test_text_file_is_rejected():
    upload = create_upload(
        filename="candidate.txt",
        content=b"Test Candidate CV",
        content_type="text/plain",
    )

    with pytest.raises(
        UnsupportedFileTypeError
    ):
        await validate_cv_upload(
            upload
        )


@pytest.mark.asyncio
async def test_declared_mime_type_mismatch_is_rejected():
    upload = create_upload(
        filename="candidate.pdf",
        content=create_pdf_bytes(),
        content_type="image/png",
    )

    with pytest.raises(
        UnsupportedFileTypeError
    ):
        await validate_cv_upload(
            upload
        )


@pytest.mark.asyncio
async def test_extension_signature_mismatch_is_rejected():
    upload = create_upload(
        filename="candidate.pdf",
        content=create_docx_bytes(),
        content_type=(
            "application/octet-stream"
        ),
    )

    with pytest.raises(
        UnsupportedFileTypeError
    ) as error:
        await validate_cv_upload(
            upload
        )

    assert (
        error.value.details[
            "declared_extension"
        ]
        == ".pdf"
    )

    assert (
        error.value.details[
            "detected_extension"
        ]
        == ".docx"
    )


@pytest.mark.asyncio
async def test_pdf_content_with_docx_extension_is_rejected():
    upload = create_upload(
        filename="candidate.docx",
        content=create_pdf_bytes(),
        content_type=(
            "application/octet-stream"
        ),
    )

    with pytest.raises(
        UnsupportedFileTypeError
    ):
        await validate_cv_upload(
            upload
        )


@pytest.mark.asyncio
async def test_invalid_pdf_signature_is_rejected():
    upload = create_upload(
        filename="candidate.pdf",
        content=b"not a valid pdf",
        content_type="application/pdf",
    )

    with pytest.raises(
        UnsupportedFileTypeError
    ):
        await validate_cv_upload(
            upload
        )


@pytest.mark.asyncio
async def test_invalid_docx_archive_is_rejected():
    upload = create_upload(
        filename="candidate.docx",
        content=b"PK invalid archive",
        content_type=(
            "application/octet-stream"
        ),
    )

    with pytest.raises(
        UnsupportedFileTypeError
    ):
        await validate_cv_upload(
            upload
        )


@pytest.mark.asyncio
async def test_oversized_file_is_rejected():
    upload = create_upload(
        filename="candidate.pdf",
        content=(
            b"%PDF-1.7\n"
            + b"x"
            * (
                1024 * 1024 + 1
            )
        ),
        content_type="application/pdf",
    )

    with pytest.raises(
        FileTooLargeError
    ) as error:
        await validate_cv_upload(
            upload,
            max_size_mb=1,
        )

    assert (
        error.value.status_code
        == 413
    )

    assert error.value.code == (
        "FILE_TOO_LARGE"
    )


@pytest.mark.asyncio
async def test_file_at_size_limit_is_not_rejected_as_oversized():
    pdf_header = b"%PDF-1.7\n"

    content = (
        pdf_header
        + b"x"
        * (
            1024 * 1024
            - len(pdf_header)
        )
    )

    upload = create_upload(
        filename="candidate.pdf",
        content=content,
        content_type="application/pdf",
    )

    validated = await validate_cv_upload(
        upload,
        max_size_mb=1,
    )

    assert validated.size_bytes == (
        1024 * 1024
    )


@pytest.mark.asyncio
async def test_upload_stream_is_reset_after_validation():
    upload = create_upload(
        filename="candidate.pdf",
        content=create_pdf_bytes(),
        content_type="application/pdf",
    )

    await validate_cv_upload(
        upload
    )

    first_bytes = await upload.read(5)

    assert first_bytes == b"%PDF-"