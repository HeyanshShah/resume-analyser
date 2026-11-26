"""Figure out which job-posting skills are required vs. nice-to-have.

Postings signal importance two ways, and we read both:
  1. Section headers: "Requirements" / "Minimum qualifications" vs. "Preferred" / "Bonus".
  2. Cue phrases in the sentence itself: "must have", "required" vs. "a plus",
     "nice to have", "familiarity with", "preferred".
Weights: required 1.0, unmarked 0.75, preferred 0.5. A skill mentioned in several
places keeps its highest weight.
"""
import re

WEIGHT = {"required": 1.0, "general": 0.75, "preferred": 0.5}

REQ_HEADER = re.compile(r"\b(requirements?|required|qualifications|must[- ]haves?|what you('ll)? need|"
                        r"minimum|basic qualifications|you have|who you are)\b", re.I)
PREF_HEADER = re.compile(r"\b(preferred|nice[- ]to[- ]haves?|bonus|pluses|desired|extra credit|"
                         r"good to have|preferred qualifications)\b", re.I)
NEUTRAL_HEADER = re.compile(r"\b(responsibilities|what you('ll)? do|about (the role|us)|the role|"
                            r"benefits|perks|duties)\b", re.I)
REQ_CUE = re.compile(r"\b(must|required|requires|minimum|essential|mandatory|need to have)\b", re.I)
PREF_CUE = re.compile(r"\b(a plus|is a plus|nice to have|bonus|preferred|ideally|familiarity|"
                      r"exposure to|desired|helpful|advantage)\b", re.I)


def _is_header(line: str) -> bool:
    words = line.split()
    return 0 < len(words) <= 6 and (line.endswith(":") or line.istitle() or line.isupper()
                                    or not re.search(r"[.,;]", line))


def classify_lines(jd_text: str) -> list[tuple[str, str]]:
    """Return [(line, importance)] for every non-header line."""
    section = "general"
    out = []
    for raw in jd_text.split("\n"):
        line = raw.strip(" -•*●\t")
        if not line:
            continue
        if _is_header(line):
            if PREF_HEADER.search(line):
                section = "preferred"
            elif REQ_HEADER.search(line):
                section = "required"
            elif NEUTRAL_HEADER.search(line):
                section = "general"
            if len(line.split()) <= 4:
                continue
        # Judge each sentence separately: one paragraph often mixes "must" and "a plus".
        for sent in re.split(r"(?<=[.!?;])\s+", line):
            if not sent.strip():
                continue
            importance = section
            if PREF_CUE.search(sent):
                importance = "preferred"
            elif REQ_CUE.search(sent):
                importance = "required"
            out.append((sent, importance))
    return out


def skill_weights(jd_text: str, find_skills) -> dict[str, tuple[float, str]]:
    weights: dict[str, tuple[float, str]] = {}
    for line, importance in classify_lines(jd_text):
        for skill in find_skills(line):
            w = WEIGHT[importance]
            if skill not in weights or w > weights[skill][0]:
                weights[skill] = (w, importance)
    return weights
