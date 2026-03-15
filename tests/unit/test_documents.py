"""Unit tests for document upload validation and prompt helpers."""

from __future__ import annotations

import pytest
from src.core.documents import (
    DocumentUploadInput,
    DocumentValidationError,
    build_document_prompt_addendum,
    validate_document_uploads,
)

pytestmark = pytest.mark.unit


def test_validate_document_uploads_accepts_supported_pdf() -> None:
    uploads = [
        DocumentUploadInput(
            name="BAfoeG-Bescheid.pdf",
            media_type="application/pdf",
            content=b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n",
        )
    ]

    validated = validate_document_uploads(uploads)

    assert len(validated) == 1
    assert validated[0].extension == "pdf"
    assert validated[0].name == "BAfoeG-Bescheid.pdf"


def test_validate_document_uploads_rejects_unsupported_extension() -> None:
    uploads = [
        DocumentUploadInput(
            name="notes.exe",
            media_type="application/octet-stream",
            content=b"not really executable",
        )
    ]

    with pytest.raises(DocumentValidationError, match="Unsupported file type"):
        validate_document_uploads(uploads)


def test_validate_document_uploads_rejects_encrypted_pdf() -> None:
    uploads = [
        DocumentUploadInput(
            name="secret.pdf",
            media_type="application/pdf",
            content=b"%PDF-1.4\n/Encrypt true\n",
        )
    ]

    with pytest.raises(DocumentValidationError, match="password-protected or encrypted"):
        validate_document_uploads(uploads)


def test_build_document_prompt_addendum_mentions_attached_and_remembered_docs() -> None:
    addendum = build_document_prompt_addendum(
        {
            "attached": ("BAfoeG-Bescheid.pdf",),
            "remembered": ("Modulhandbuch.pdf (PDF)",),
        }
    )

    assert "Documents attached in this turn" in addendum
    assert "BAfoeG-Bescheid.pdf" in addendum
    assert "Modulhandbuch.pdf (PDF)" in addendum
    assert "Treat uploaded documents as user-provided evidence" in addendum
