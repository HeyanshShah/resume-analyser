"""Step 2: skills matching that understands synonyms, word forms, and importance.

* Ontology (ontology.json): ~140 canonical skills, each with aliases and a family.
  "JS" -> JavaScript, "k8s" -> Kubernetes, "Postgres" -> PostgreSQL, "helpdesk" -> help desk.
* Lemma matching: "troubleshooting", "troubleshot" and "troubleshoot" all match.
* Short/ambiguous names ("Go", "R", "C") are matched case-sensitively, so the verb
  "go" isn't mistaken for the Go language.
* Partial credit: if the job wants MySQL and you list PostgreSQL (same family:
  relational database), that's half a match instead of zero.
"""
from functools import lru_cache
import json
from pathlib import Path

from spacy.matcher import PhraseMatcher

from .nlp import get_nlp
from .requirements import skill_weights

ONTOLOGY = json.loads(Path(__file__).with_name("ontology.json").read_text())
CASE_SENSITIVE = {"Go", "R", "C", "Swift", "Express", "Spark", "Rust", "Excel", "Claude", "Scala"}
PARTIAL_CREDIT = 0.5
# Families whose members can substitute for each other (knowing Postgres means you can
# pick up MySQL fast). Languages, soft skills, etc. don't get partial credit.
SUBSTITUTES = {"relational database", "nosql database", "frontend", "backend", "cloud provider",
               "bi tool", "mdm", "itsm tool", "ml framework", "ci tool", "testing"}


@lru_cache(maxsize=1)
def matchers():
    nlp = get_nlp()
    lower = PhraseMatcher(nlp.vocab, attr="LOWER")
    exact = PhraseMatcher(nlp.vocab, attr="ORTH")
    lemma = PhraseMatcher(nlp.vocab, attr="LEMMA")
    for skill, info in ONTOLOGY.items():
        terms = [skill] + info["aliases"]
        for term in terms:
            if term in CASE_SENSITIVE or (len(term) <= 2 and term[:1].isupper()):
                exact.add(skill, [nlp.make_doc(term)])
            else:
                lower.add(skill, [nlp.make_doc(term)])
                if term.islower() and term.replace(" ", "").replace("-", "").isalpha():
                    lemma.add(skill, [nlp(term)])   # needs lemmas, so run the pipeline
    return lower, exact, lemma


def find_skills(text: str) -> set[str]:
    nlp = get_nlp()
    doc = nlp(text)
    found = set()
    for m in matchers():
        for match_id, _, _ in m(doc):
            found.add(nlp.vocab.strings[match_id])
    return found


def family(skill: str) -> str:
    return ONTOLOGY.get(skill, {}).get("family", "")


def keyword_coverage(resume_text: str, jd_text: str) -> dict:
    weights = skill_weights(jd_text, find_skills)       # skill -> (weight, importance)
    resume_skills = find_skills(resume_text)
    resume_families = {family(s) for s in resume_skills}
    matched, partial, missing = [], [], []
    earned = total = 0.0
    for skill, (w, importance) in sorted(weights.items(), key=lambda kv: (-kv[1][0], kv[0].lower())):
        total += w
        row = {"skill": skill, "importance": importance, "family": family(skill)}
        if skill in resume_skills:
            earned += w
            matched.append(row)
        elif family(skill) in resume_families and family(skill) in SUBSTITUTES:
            earned += w * PARTIAL_CREDIT
            similar = sorted(s for s in resume_skills if family(s) == family(skill))
            partial.append({**row, "you_have": ", ".join(similar[:3])})
        else:
            missing.append(row)
    return {
        "coverage": earned / total if total else 0.0,
        "matched": matched, "partial": partial, "missing": missing,
        "required_missing": [m["skill"] for m in missing if m["importance"] == "required"],
        "resume_skills": sorted(resume_skills, key=str.lower),
    }
