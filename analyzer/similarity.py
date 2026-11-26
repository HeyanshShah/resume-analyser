"""Step 3: measure how similar the resume's *meaning* is to the job description.

Keyword matching misses synonyms ("built dashboards" vs "data visualization").
Embeddings fix that: a model turns each text into a list of numbers (a vector)
where texts with similar meaning end up close together. We compare the two
vectors with cosine similarity (1.0 = same direction, 0 = unrelated).

Primary method: sentence-transformers (all-MiniLM-L6-v2), a small, fast model.
Fallback: TF-IDF vectors from scikit-learn, used if the model isn't installed
or can't be downloaded, so the app always works.
"""
from functools import lru_cache
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(MODEL_NAME)
    except Exception:  # not installed, or no internet to download the model
        return None


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def split_chunks(text: str, max_words: int = 60) -> list[str]:
    """Split long text into ~60-word chunks (the model works best on short passages)."""
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    chunks, current = [], []
    for s in sentences:
        current.extend(s.split())
        while len(current) >= max_words:
            chunks.append(" ".join(current[:max_words]))
            current = current[max_words:]
    if current:
        chunks.append(" ".join(current))
    return [c for c in chunks if c.strip()] or [text]


def semantic_similarity(resume_text: str, jd_text: str) -> tuple[float, str]:
    """Return (similarity 0..1, method used)."""
    model = _load_model()
    if model is not None:
        # Average the chunk embeddings so long documents are represented fairly.
        r = model.encode(split_chunks(resume_text)).mean(axis=0)
        j = model.encode(split_chunks(jd_text)).mean(axis=0)
        return max(0.0, cosine(r, j)), "embeddings"

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    m = vec.fit_transform([resume_text, jd_text]).toarray()
    return cosine(m[0], m[1]), "tfidf"


def merge_wrapped_lines(text: str) -> list[str]:
    """PDFs wrap long bullets onto several lines. A line starting with a lowercase
    letter (or after a line ending in a comma) is a continuation, so glue it back."""
    merged: list[str] = []
    for line in (l.strip() for l in text.split("\n")):
        if not line:
            continue
        if merged and (line[0].islower() or merged[-1].endswith((",", "-", "("))):
            merged[-1] += " " + line
        else:
            merged.append(line)
    return merged


def best_matching_lines(resume_text: str, jd_text: str, top: int = 3) -> list[tuple[str, float]]:
    """Which resume lines are most relevant to this job? Useful for feedback."""
    lines = [l for l in merge_wrapped_lines(resume_text) if len(l.split()) >= 6]
    if not lines:
        return []
    model = _load_model()
    if model is not None:
        jd_vec = model.encode([jd_text])[0]
        scores = [cosine(v, jd_vec) for v in model.encode(lines)]
    else:
        vec = TfidfVectorizer(stop_words="english").fit(lines + [jd_text])
        jd_vec = vec.transform([jd_text]).toarray()[0]
        scores = [cosine(v, jd_vec) for v in vec.transform(lines).toarray()]
    ranked = sorted(zip(lines, scores), key=lambda x: -x[1])
    return ranked[:top]
