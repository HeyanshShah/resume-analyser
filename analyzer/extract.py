"""Step 1: get plain text out of a resume file.

PDFs store text as positioned characters, not paragraphs, so we use PDFMiner
to rebuild readable text. Plain .txt files are read directly.
"""
from io import BytesIO
import re

from pdfminer.high_level import extract_text as _pdf_extract


def extract_text(data: bytes, filename: str) -> str:
    """Return cleaned text from an uploaded file's raw bytes."""
    name = filename.lower()
    if name.endswith(".pdf"):
        text = _pdf_extract(BytesIO(data))
    elif name.endswith(".txt"):
        text = data.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file type. Upload a .pdf or .txt file.")
    return clean_text(text)


def clean_text(text: str) -> str:
    """Normalize bullets, odd whitespace, and line breaks from PDF extraction."""
    text = text.replace("•", " ").replace("●", " ").replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)
