"""
app/resume_parser.py
====================
Format-agnostic resume text extraction.

Supports PDF (via PyPDF2), Word DOCX (via python-docx), and plain TXT.
All public functions accept a binary file-like object so they work with
both Streamlit UploadedFile objects and regular open() file handles.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, BinaryIO

from PyPDF2 import PdfReader
from docx import Document


def _read_all_bytes(file_obj: BinaryIO) -> bytes:
    """Read all bytes from a file-like object, encoding str to UTF-8 if needed."""
    data = file_obj.read()
    if isinstance(data, str):
        data = data.encode("utf-8", errors="ignore")
    return data


def extract_text_from_pdf(file_obj: BinaryIO) -> str:
    """Extract plain text from all pages of a PDF file object."""
    data = _read_all_bytes(file_obj)
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        parts.append(text)
    return "\n".join(parts)


def extract_text_from_docx(file_obj: BinaryIO) -> str:
    """Extract plain text from a DOCX file object by joining non-empty paragraphs."""
    data = _read_all_bytes(file_obj)
    document = Document(io.BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_txt(file_obj: BinaryIO) -> str:
    """Decode a plain-text file object, falling back to latin-1 if UTF-8 fails."""
    data = _read_all_bytes(file_obj)
    try:
        return data.decode("utf-8")
    except Exception:
        return data.decode("latin-1", errors="ignore")


def extract_resume_text(uploaded_file: Any) -> str:
    """
    Dispatch to the correct extractor based on the uploaded file's extension.

    Accepts a Streamlit UploadedFile object. Supports .pdf, .docx, and .txt.
    Falls back to plain-text decoding for unrecognised formats.
    """
    name = uploaded_file.name or ""
    suffix = Path(name.lower()).suffix

    if suffix == ".pdf":
        return extract_text_from_pdf(uploaded_file)
    if suffix in {".docx"}:
        return extract_text_from_docx(uploaded_file)
    if suffix in {".txt"}:
        return extract_text_from_txt(uploaded_file)

    # Fallback: try plain text first, then PDF
    try:
        return extract_text_from_txt(uploaded_file)
    except Exception:
        try:
            return extract_text_from_pdf(uploaded_file)
        except Exception:
            return ""

