from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

from PyPDF2 import PdfReader
from docx import Document


def _read_all_bytes(file_obj: BinaryIO) -> bytes:
    data = file_obj.read()
    if isinstance(data, str):
        data = data.encode("utf-8", errors="ignore")
    return data


def extract_text_from_pdf(file_obj: BinaryIO) -> str:
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
    data = _read_all_bytes(file_obj)
    document = Document(io.BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_txt(file_obj: BinaryIO) -> str:
    data = _read_all_bytes(file_obj)
    try:
        return data.decode("utf-8")
    except Exception:
        return data.decode("latin-1", errors="ignore")


def extract_resume_text(uploaded_file) -> str:
    """
    Streamlit `UploadedFile` wrapper that dispatches based on file extension.
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

