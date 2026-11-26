"""Step 1: get text out of a resume, and split it into sections and bullet points.

PDFs store characters at positions on a page, not paragraphs, so PDFMiner rebuilds
lines; we then glue wrapped lines back into whole bullets.
"""
from io import BytesIO
import re

from pdfminer.high_level import extract_text as _pdf_extract

BULLET_CHARS = "•●▪◦‣∙·-–*"
SECTION_WORDS = {
    "experience": "experience", "work experience": "experience", "professional experience": "experience",
    "employment": "experience", "projects": "projects", "personal projects": "projects",
    "academic projects": "projects", "education": "education", "skills": "skills",
    "technical skills": "skills", "leadership": "activities", "activities": "activities",
    "extracurricular activities": "activities", "volunteer": "activities", "summary": "summary",
    "certifications": "certifications", "awards": "awards",
}
BULLET_SECTIONS = {"experience", "projects", "activities"}
DATE_RE = re.compile(r"(19|20)\d{2}|present", re.I)


def extract_text(data: bytes, filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        text = _pdf_extract(BytesIO(data))
    elif name.endswith((".txt", ".md")):
        text = data.decode("utf-8", errors="ignore")
    elif name.endswith(".docx"):
        from docx import Document  # python-docx
        text = "\n".join(p.text for p in Document(BytesIO(data)).paragraphs)
    else:
        raise ValueError("Unsupported file type. Upload a .pdf, .docx, or .txt file.")
    return text.replace("\x0c", "\n")


def clean_text(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", l.strip(" " + BULLET_CHARS)) for l in text.split("\n")]
    return "\n".join(l for l in lines if l)


def _section_of(line: str):
    key = re.sub(r"[^a-z ]", "", line.lower()).strip()
    if key in SECTION_WORDS and len(line) < 40:
        return SECTION_WORDS[key]
    return None


def split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        sec = _section_of(line)
        if sec:
            current = sec
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _is_title_line(line: str) -> bool:
    """Job titles, project names, and date lines are not bullets."""
    words = line.split()
    if "|" in line or len(words) < 6:
        return True
    if (" — " in line or " – " in line) and not line.endswith("."):
        return True  # "Job Title — Company, City"
    if DATE_RE.search(line) and len(words) < 12 and not line.endswith("."):
        return True
    return False


def extract_bullets(text: str) -> list[dict]:
    """Return [{"section": ..., "text": ...}] for every bullet in bullet-style sections.
    Handles explicit bullet symbols and PDFs where symbols were lost: a line that starts
    lowercase, or follows a line without ending punctuation, is a continuation."""
    out = []
    for section, lines in split_sections(text).items():
        if section not in BULLET_SECTIONS:
            continue
        current = None
        for raw in lines:
            has_marker = raw[:1] in BULLET_CHARS
            line = raw.strip(" " + BULLET_CHARS)
            if not line:
                continue
            continuation = (current is not None and not has_marker and
                            (line[0].islower() or not current["text"].rstrip().endswith((".", "!", "?"))))
            if continuation and not _is_title_line(line) or (continuation and line[0].islower()):
                current["text"] += " " + line
                continue
            if _is_title_line(line) and not has_marker:
                current = None
                continue
            current = {"section": section, "text": line}
            out.append(current)
    for b in out:
        b["text"] = re.sub(r"\s+", " ", b["text"]).strip()
    return [b for b in out if len(b["text"].split()) >= 5]
