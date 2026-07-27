import re
import secrets
import unicodedata
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePath

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)


READ_CHUNK_SIZE = 1024 * 1024

ALLOWED_CV_EXTENSIONS = {
    ".pdf",
    ".docx",
}

ALLOWED_CONTENT_TYPES = {
    ".pdf": {
        "application/pdf",
        "application/x-pdf",
    },
    ".docx": {
        (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        "application/zip",
    },
}

GENERIC_CONTENT_TYPES = {
    "",
    "application/octet-stream",
    "binary/octet-stream",
}

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


@dataclass(
    frozen=True,
    slots=True,
)
class ValidatedCVUpload:
    """
    Represents a CV upload that has passed security
    validation.
    """

    original_filename: str
    safe_filename: str
    storage_filename: str
    extension: str
    content_type: str
    content: bytes
    size_bytes: int


def sanitize_filename(
    filename: str,
) -> str:
    """
    Remove directory traversal, null bytes and unsafe
    characters from an uploaded filename.
    """

    normalized = unicodedata.normalize(
        "NFKC",
        filename or "",
    )

    normalized = normalized.replace(
        "\x00",
        "",
    )

    normalized = normalized.replace(
        "\\",
        "/",
    )

    basename = PurePath(
        normalized
    ).name.strip()

    # Handle filenames containing only an extension,
    # such as ".pdf" or ".docx".
    if (
        basename.lower()
        in ALLOWED_CV_EXTENSIONS
    ):
        extension = basename.lower()
        stem = ""

    else:
        path = Path(
            basename
        )

        extension = path.suffix.lower()
        stem = path.stem

    safe_stem = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        stem,
    )

    safe_stem = safe_stem.strip(
        "._-"
    )

    if not safe_stem:
        safe_stem = "cv"

    if (
        safe_stem.upper()
        in WINDOWS_RESERVED_NAMES
    ):
        safe_stem = (
            f"cv_{safe_stem.lower()}"
        )

    safe_stem = safe_stem[:80]

    return (
        f"{safe_stem}{extension}"
    )


def _normalise_content_type(
    content_type: str | None,
) -> str:
    """
    Remove optional MIME parameters and return a
    lowercase content type.
    """

    return (
        str(content_type or "")
        .split(";", maxsplit=1)[0]
        .strip()
        .lower()
    )


def _validate_declared_content_type(
    extension: str,
    content_type: str,
) -> None:
    """
    Confirm that the declared MIME type is compatible
    with the uploaded filename extension.
    """

    if (
        content_type
        in GENERIC_CONTENT_TYPES
    ):
        return

    allowed_types = (
        ALLOWED_CONTENT_TYPES[
            extension
        ]
    )

    if content_type not in allowed_types:
        raise UnsupportedFileTypeError(
            (
                "The declared file type does not "
                "match an allowed CV format."
            ),
            details={
                "extension": extension,
                "content_type": content_type,
            },
        )


def _validate_docx_archive(
    content: bytes,
    *,
    max_uncompressed_mb: int,
) -> bool:
    """
    Confirm that ZIP content is a genuine DOCX archive.

    The checks also prevent unsafe paths, encrypted
    archives, excessive entries and excessive expanded
    archive size.
    """

    stream = BytesIO(
        content
    )

    if not zipfile.is_zipfile(
        stream
    ):
        return False

    stream.seek(0)

    try:
        with zipfile.ZipFile(
            stream
        ) as archive:
            entries = (
                archive.infolist()
            )

            if len(entries) > 5_000:
                raise BadRequestError(
                    (
                        "The DOCX file contains too "
                        "many archive entries."
                    )
                )

            total_uncompressed_size = sum(
                entry.file_size
                for entry in entries
            )

            maximum_uncompressed_size = (
                max_uncompressed_mb
                * 1024
                * 1024
            )

            if (
                total_uncompressed_size
                > maximum_uncompressed_size
            ):
                raise BadRequestError(
                    (
                        "The expanded DOCX file exceeds "
                        "the permitted processing size."
                    ),
                    details={
                        "maximum_uncompressed_bytes": (
                            maximum_uncompressed_size
                        ),
                    },
                )

            archive_names: set[str] = set()

            for entry in entries:
                entry_name = (
                    entry.filename.replace(
                        "\\",
                        "/",
                    )
                )

                entry_path = PurePath(
                    entry_name
                )

                if (
                    entry_name.startswith("/")
                    or ".." in entry_path.parts
                ):
                    raise BadRequestError(
                        (
                            "The DOCX archive contains "
                            "an unsafe internal path."
                        )
                    )

                if entry.flag_bits & 0x1:
                    raise BadRequestError(
                        (
                            "Encrypted DOCX archives "
                            "are not supported."
                        )
                    )

                archive_names.add(
                    entry_name
                )

            required_entries = {
                "[Content_Types].xml",
                "_rels/.rels",
                "word/document.xml",
            }

            return (
                required_entries.issubset(
                    archive_names
                )
            )

    except zipfile.BadZipFile:
        return False


def _detect_file_type(
    content: bytes,
    *,
    max_docx_uncompressed_mb: int,
) -> str | None:
    """
    Detect PDF or DOCX content from its signature and
    internal document structure.
    """

    if content.startswith(
        b"%PDF-"
    ):
        return ".pdf"

    if content.startswith(
        b"PK"
    ):
        is_docx = (
            _validate_docx_archive(
                content,
                max_uncompressed_mb=(
                    max_docx_uncompressed_mb
                ),
            )
        )

        if is_docx:
            return ".docx"

    return None


async def _read_upload_content(
    upload: UploadFile,
    *,
    maximum_size_bytes: int,
) -> bytes:
    """
    Read an uploaded file in chunks while enforcing the
    maximum permitted size.
    """

    chunks: list[bytes] = []
    total_size = 0

    try:
        while True:
            chunk = await upload.read(
                READ_CHUNK_SIZE
            )

            if not chunk:
                break

            total_size += len(
                chunk
            )

            if (
                total_size
                > maximum_size_bytes
            ):
                raise FileTooLargeError(
                    (
                        "The uploaded CV exceeds "
                        "the permitted size."
                    ),
                    details={
                        "maximum_size_bytes": (
                            maximum_size_bytes
                        ),
                        "received_size_bytes": (
                            total_size
                        ),
                    },
                )

            chunks.append(
                chunk
            )

    finally:
        # Reset the stream so another service can read
        # the file after validation.
        await upload.seek(0)

    return b"".join(
        chunks
    )


async def validate_cv_upload(
    upload: UploadFile,
    *,
    max_size_mb: int | None = None,
    max_docx_uncompressed_mb: int | None = None,
) -> ValidatedCVUpload:
    """
    Validate an uploaded CV using:

    - Filename and extension
    - Declared MIME type
    - Actual file signature
    - DOCX archive structure
    - Upload size
    - Expanded DOCX size
    """

    original_filename = (
        upload.filename or ""
    ).strip()

    if not original_filename:
        raise BadRequestError(
            "The uploaded CV must have a filename."
        )

    normalized_name = (
        original_filename.replace(
            "\\",
            "/",
        )
    )

    basename = PurePath(
        normalized_name
    ).name

    extension = Path(
        basename
    ).suffix.lower()

    if (
        extension
        not in ALLOWED_CV_EXTENSIONS
    ):
        raise UnsupportedFileTypeError(
            (
                "Only PDF and DOCX CV files "
                "are supported."
            ),
            details={
                "allowed_extensions": [
                    ".pdf",
                    ".docx",
                ],
            },
        )

    content_type = (
        _normalise_content_type(
            upload.content_type
        )
    )

    _validate_declared_content_type(
        extension,
        content_type,
    )

    effective_max_size_mb = (
        max_size_mb
        if max_size_mb is not None
        else settings.MAX_UPLOAD_SIZE_MB
    )

    if effective_max_size_mb < 1:
        raise ValueError(
            "max_size_mb must be at least 1."
        )

    maximum_size_bytes = (
        effective_max_size_mb
        * 1024
        * 1024
    )

    content = await _read_upload_content(
        upload,
        maximum_size_bytes=(
            maximum_size_bytes
        ),
    )

    if not content:
        raise BadRequestError(
            "The uploaded CV is empty."
        )

    effective_docx_limit = (
        max_docx_uncompressed_mb
        if (
            max_docx_uncompressed_mb
            is not None
        )
        else settings.MAX_DOCX_UNCOMPRESSED_MB
    )

    if effective_docx_limit < 1:
        raise ValueError(
            (
                "max_docx_uncompressed_mb "
                "must be at least 1."
            )
        )

    detected_extension = (
        _detect_file_type(
            content,
            max_docx_uncompressed_mb=(
                effective_docx_limit
            ),
        )
    )

    if detected_extension is None:
        raise UnsupportedFileTypeError(
            (
                "The uploaded file content is not "
                "a valid PDF or DOCX document."
            )
        )

    if (
        detected_extension
        != extension
    ):
        raise UnsupportedFileTypeError(
            (
                "The uploaded file extension does not "
                "match its actual document format."
            ),
            details={
                "declared_extension": extension,
                "detected_extension": (
                    detected_extension
                ),
            },
        )

    safe_filename = sanitize_filename(
        original_filename
    )

    storage_filename = (
        f"{secrets.token_hex(16)}"
        f"{extension}"
    )

    return ValidatedCVUpload(
        original_filename=(
            original_filename
        ),
        safe_filename=safe_filename,
        storage_filename=(
            storage_filename
        ),
        extension=extension,
        content_type=content_type,
        content=content,
        size_bytes=len(content),
    )