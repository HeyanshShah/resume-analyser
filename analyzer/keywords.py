"""Step 2: pull out the keywords an ATS (applicant tracking system) looks for.

Two sources of keywords:
  1. A curated skills dictionary (skills.txt), matched with spaCy's PhraseMatcher,
     so "Node.js", "machine learning", "Active Directory" are caught as one term.
  2. spaCy noun chunks and named entities from the job description, which catch
     role-specific terms that aren't in the dictionary (e.g. "ticket triage").
"""
from functools import lru_cache
from pathlib import Path
import re

import spacy
from spacy.matcher import PhraseMatcher

SKILLS_FILE = Path(__file__).with_name("skills.txt")

# Words that show up in every job post but are not skills.
GENERIC = {
    "experience", "ability", "team", "work", "role", "candidate", "company", "years",
    "skills", "knowledge", "position", "opportunity", "responsibilities", "requirements",
    "student", "students", "you", "we", "they", "it", "this", "that", "who", "what",
    "the ability", "a variety", "our team", "the role", "internship", "intern", "job",
    "benefits", "salary", "location", "equal opportunity", "employer", "plus", "bonus",
    "degree", "summer", "field", "fields", "related field", "employees", "software",
    "hardware", "requirements", "responsibilities", "tasks", "issues", "users", "people",
    "day", "time", "year", "month", "week", "hours", "office", "teams", "member",
}


@lru_cache(maxsize=1)
def get_nlp():
    """Load the spaCy English model once and reuse it (loading is slow)."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        # Model not downloaded: fall back to a blank pipeline so the app still runs.
        nlp = spacy.blank("en")
        return nlp


@lru_cache(maxsize=1)
def load_skills() -> tuple[str, ...]:
    lines = SKILLS_FILE.read_text(encoding="utf-8").splitlines()
    return tuple(s.strip() for s in lines if s.strip() and not s.startswith("#"))


@lru_cache(maxsize=1)
def get_matcher() -> PhraseMatcher:
    nlp = get_nlp()
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")  # case-insensitive
    matcher.add("SKILL", [nlp.make_doc(s) for s in load_skills()])
    return matcher


def _canonical(term: str) -> str:
    """Map matched text back to the dictionary's spelling ("python" -> "Python")."""
    lookup = {s.lower(): s for s in load_skills()}
    return lookup.get(term.lower(), term)


def find_skills(text: str) -> set[str]:
    """Return dictionary skills that appear in the text."""
    nlp = get_nlp()
    doc = nlp.make_doc(text)
    return {_canonical(doc[s:e].text) for _, s, e in get_matcher()(doc)}


def find_phrases(text: str, limit: int = 25) -> list[str]:
    """Return frequent noun phrases / entities from a job description.

    Only works when the full spaCy model is installed (blank pipelines have no parser).
    """
    nlp = get_nlp()
    if "parser" not in nlp.pipe_names:
        return []
    # Treat line breaks as sentence ends so headings don't merge with the next line.
    doc = nlp(re.sub(r"\s*\n\s*", ". ", text))
    counts: dict[str, int] = {}
    candidates = [c.text for c in doc.noun_chunks] + [e.text for e in doc.ents
                                                       if e.label_ in {"ORG", "PRODUCT"}]
    for raw in candidates:
        phrase = " ".join(raw.lower().split())  # collapse newlines/extra spaces
        phrase = re.sub(r"^(a|an|the|our|your|their|strong|excellent|all|any)\s+", "", phrase)
        words = phrase.split()
        if not 1 <= len(words) <= 3 or phrase in GENERIC or len(phrase) < 3:
            continue
        if any(not w.replace("-", "").isalpha() for w in words):
            continue  # skip numbers and fragments like "500 employees"
        if all(w in GENERIC for w in words):
            continue
        counts[phrase] = counts.get(phrase, 0) + 1
    ranked = sorted(counts, key=lambda p: (-counts[p], p))
    return ranked[:limit]


def keyword_coverage(resume_text: str, jd_text: str) -> dict:
    """Compare skills in the job description against skills in the resume."""
    jd_skills = find_skills(jd_text)
    resume_skills = find_skills(resume_text)
    matched = sorted(jd_skills & resume_skills, key=str.lower)
    missing = sorted(jd_skills - resume_skills, key=str.lower)
    coverage = len(matched) / len(jd_skills) if jd_skills else 0.0

    resume_lower = resume_text.lower()
    skill_words = {w for s in jd_skills for w in s.lower().split()}
    phrases = [p for p in find_phrases(jd_text)
               if not set(p.split()) <= skill_words]  # already covered as a skill
    missing_phrases = [p for p in phrases if p not in resume_lower]

    return {
        "jd_skills": sorted(jd_skills, key=str.lower),
        "matched": matched,
        "missing": missing,
        "coverage": coverage,
        "missing_phrases": missing_phrases[:10],
    }
