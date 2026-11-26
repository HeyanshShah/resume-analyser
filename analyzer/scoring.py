"""Step 4: one overall score plus specific, prioritized feedback.

Overall = 50% weighted keyword coverage (what ATS filters check)
        + 25% semantic similarity (does the resume describe this kind of work?)
        + 25% bullet quality (how a human recruiter reacts when they read it)
"""
from dataclasses import dataclass, field

from .bullets import BulletReport, analyze_bullets
from .extract import extract_bullets
from .keywords import keyword_coverage
from .similarity import best_matching_lines, semantic_similarity

WEIGHTS = {"keywords": 0.5, "semantic": 0.25, "bullets": 0.25}
SEMANTIC_CEILING = {"embeddings": 0.75, "tfidf": 0.45}


@dataclass
class Report:
    score: int
    keyword_coverage: float
    semantic: float
    bullet_quality: float
    method: str
    keywords: dict
    bullets: list[BulletReport]
    strongest_lines: list
    feedback: list = field(default_factory=list)

    @property
    def matched(self):
        return [m["skill"] for m in self.keywords["matched"]]

    @property
    def missing(self):
        return [m["skill"] for m in self.keywords["missing"]]


def analyze(resume_text: str, jd_text: str) -> Report:
    if not resume_text.strip() or not jd_text.strip():
        raise ValueError("Both the resume and the job description need text.")
    kw = keyword_coverage(resume_text, jd_text)
    raw, method = semantic_similarity(resume_text, jd_text)
    sem = min(1.0, raw / SEMANTIC_CEILING[method])
    bullets = analyze_bullets(extract_bullets(resume_text))
    bq = sum(b.score for b in bullets) / (100 * len(bullets)) if bullets else 0.5
    score = round(100 * (WEIGHTS["keywords"] * kw["coverage"] + WEIGHTS["semantic"] * sem
                         + WEIGHTS["bullets"] * bq))
    r = Report(score, kw["coverage"], sem, bq, method, kw, bullets,
               best_matching_lines(resume_text, jd_text))
    r.feedback = build_feedback(r)
    return r


def build_feedback(r: Report) -> list[str]:
    tips = []
    req = r.keywords["required_missing"]
    if req:
        tips.append(f"🚨 Missing REQUIRED skills (fix first): {', '.join(req[:8])}.")
    other = [m["skill"] for m in r.keywords["missing"] if m["importance"] != "required"]
    if other:
        tips.append(f"Also missing: {', '.join(other[:8])}.")
    for p in r.keywords["partial"][:3]:
        tips.append(f"Posting asks for {p['skill']}; you list {p['you_have']}. Mention {p['skill']} "
                    "if you've used it, or note the transferable experience.")
    if r.bullets:
        n_passive = sum(b.passive for b in r.bullets)
        n_weak = sum(not b.strong_opening for b in r.bullets)
        n_unquant = sum(not b.quantified for b in r.bullets)
        total = len(r.bullets)
        if n_weak:
            tips.append(f"{n_weak}/{total} bullets open weakly; start each with an action verb.")
        if n_passive:
            tips.append(f"{n_passive}/{total} bullets use passive voice.")
        if n_unquant / total > 0.5:
            tips.append(f"Only {total - n_unquant}/{total} bullets contain a number. Recruiters look for "
                        "scale and impact (users, %, time saved, tickets/week).")
    if r.semantic < 0.5:
        tips.append("Low semantic match: describe the same kind of work the posting describes, using its verbs.")
    if not tips:
        tips.append("Strong match. Focus on tailoring your top 3 bullets to the posting's main responsibilities.")
    return tips
