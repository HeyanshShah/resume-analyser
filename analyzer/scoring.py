"""Step 4: combine everything into one score plus readable feedback.

Overall score = 60% keyword coverage + 40% semantic similarity.
Keywords get more weight because most ATS filters are keyword-based;
semantic similarity rewards resumes that describe the right kind of work.
"""
from dataclasses import dataclass, field

from .keywords import keyword_coverage
from .similarity import best_matching_lines, semantic_similarity

KEYWORD_WEIGHT = 0.6
SEMANTIC_WEIGHT = 0.4

# Raw cosine scores between two different documents rarely go above ~0.7,
# so we rescale them onto 0..1 to make the number intuitive.
SEMANTIC_CEILING = {"embeddings": 0.75, "tfidf": 0.45}


@dataclass
class Report:
    score: int
    keyword_coverage: float
    semantic: float
    method: str
    matched: list[str]
    missing: list[str]
    missing_phrases: list[str]
    strongest_lines: list[tuple[str, float]]
    feedback: list[str] = field(default_factory=list)


def analyze(resume_text: str, jd_text: str) -> Report:
    if not resume_text.strip() or not jd_text.strip():
        raise ValueError("Both the resume and the job description need text.")

    kw = keyword_coverage(resume_text, jd_text)
    raw_sem, method = semantic_similarity(resume_text, jd_text)
    sem = min(1.0, raw_sem / SEMANTIC_CEILING[method])

    score = round(100 * (KEYWORD_WEIGHT * kw["coverage"] + SEMANTIC_WEIGHT * sem))
    report = Report(
        score=score,
        keyword_coverage=kw["coverage"],
        semantic=sem,
        method=method,
        matched=kw["matched"],
        missing=kw["missing"],
        missing_phrases=kw["missing_phrases"],
        strongest_lines=best_matching_lines(resume_text, jd_text),
    )
    report.feedback = build_feedback(report)
    return report


def build_feedback(r: Report) -> list[str]:
    tips = []
    if r.score >= 75:
        tips.append("Strong match. Focus on tailoring bullet wording to the posting.")
    elif r.score >= 50:
        tips.append("Decent match. Adding the missing keywords below should push you higher.")
    else:
        tips.append("Weak match. This resume reads like a different role; tailor it heavily.")

    if r.missing:
        top = ", ".join(r.missing[:8])
        tips.append(f"Add these skills from the posting (in Skills or in a bullet): {top}.")
    if r.missing_phrases:
        tips.append("The posting repeats these phrases that your resume never uses: "
                    + ", ".join(r.missing_phrases[:5]) + ".")
    if r.semantic < 0.5:
        tips.append("Rewrite 2-3 bullets to describe the same kind of work the posting "
                    "describes, using its verbs.")
    return tips
