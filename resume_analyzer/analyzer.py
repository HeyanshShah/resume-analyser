import re
from collections import Counter
from pathlib import Path


COMMON_SKILLS = {
    "python": 5,
    "flask": 5,
    "django": 4,
    "sql": 5,
    "mysql": 4,
    "postgresql": 4,
    "rest": 5,
    "api": 4,
    "apis": 4,
    "docker": 5,
    "kubernetes": 4,
    "aws": 4,
    "azure": 4,
    "gcp": 3,
    "javascript": 4,
    "react": 4,
    "node": 4,
    "java": 4,
    "c++": 3,
    "c#": 3,
    "machine learning": 5,
    "data science": 5,
    "leadership": 4,
    "agile": 4,
    "project management": 4,
    "communication": 3,
    "teamwork": 3,
    "analytical": 3,
    "problem solving": 4,
    "testing": 3,
    "debugging": 3,
    "linux": 3,
    "git": 3,
    "microservices": 4,
    "ci/cd": 4,
    "devops": 4,
    "data analysis": 3,
    "statistics": 3,
    "excel": 2,
    "power bi": 3,
    "tableau": 3,
}


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9#+\s]", " ", text)
    text = re.sub(r"\bapis\b", "api", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str):
    normalized = normalize_text(text)
    filtered = [word for word in normalized.split() if len(word) > 2]

    terms = []
    for skill in sorted(COMMON_SKILLS, key=len, reverse=True):
        pattern = rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])"
        if re.search(pattern, normalized):
            terms.append(skill)

    counter = Counter(filtered)
    top_terms = [term for term, _ in counter.most_common(10)]

    for term in top_terms:
        if term not in terms and len(term) > 3:
            terms.append(term)

    return list(dict.fromkeys(terms))


def extract_text_from_file(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".rtf"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        try:
            import PyPDF2
        except ModuleNotFoundError as exc:
            raise RuntimeError("PDF support requires PyPDF2. Install it with: pip install PyPDF2") from exc
        reader = PyPDF2.PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    if suffix in {".doc", ".docx"}:
        try:
            import docx
        except ModuleNotFoundError as exc:
            raise RuntimeError("DOCX support requires python-docx. Install it with: pip install python-docx") from exc
        doc = docx.Document(str(path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    return path.read_text(encoding="utf-8", errors="ignore")


def score_resume(resume_text: str, job_description: str):
    resume_norm = normalize_text(resume_text)
    job_norm = normalize_text(job_description)

    resume_keywords = set(extract_keywords(resume_text))
    job_keywords = set(extract_keywords(job_description))

    matched = sorted(resume_keywords.intersection(job_keywords), key=lambda x: (-COMMON_SKILLS.get(x, 1), x))
    missing = sorted(job_keywords - resume_keywords)

    if not job_keywords:
        score = 0
        coverage = 0.0
    else:
        weighted_match = sum(COMMON_SKILLS.get(skill, 1) for skill in matched)
        weighted_total = sum(COMMON_SKILLS.get(skill, 1) for skill in job_keywords)
        coverage = weighted_match / weighted_total if weighted_total else 0.0
        score = round(max(0, min(100, coverage * 100)))

    summary = {
        "matched_skills": matched,
        "missing_skills": missing,
        "coverage": round(coverage, 2),
        "score": score,
        "resume_keywords": sorted(resume_keywords),
        "job_keywords": sorted(job_keywords),
        "resume_word_count": len(resume_norm.split()),
        "job_word_count": len(job_norm.split()),
    }
    return summary, score
