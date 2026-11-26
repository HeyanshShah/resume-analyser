"""Linguistic analysis of resume bullets.

Recruiters skim, so each bullet should open with a strong action verb, be in active
voice, show impact (ideally a number), and avoid filler. We check those with spaCy's
part-of-speech tags and dependency parse (the grammatical structure of the sentence):

  * Passive voice  -> the parser marks passive subjects/auxiliaries (nsubjpass, auxpass):
                      "Tickets were resolved by me" instead of "Resolved tickets".
  * Opening verb   -> first token's part of speech; flags weak verbs ("Helped", "Worked")
                      and weak openings ("Responsible for", "Tasked with").
  * Quantified     -> numbers, percentages, money, multipliers ("3x", "40%", "$2K", "500+").
  * Filler/hedges  -> words that add length but no information ("various", "successfully").
  * Pronouns       -> resumes drop "I/my/we".
  * Length         -> 8-32 words reads well on a one-page resume.
"""
from dataclasses import dataclass, field
import re

from .nlp import get_nlp

# Recruiter-favored action verbs (lemmas). A first word in this list counts as strong
# even when the small spaCy model mis-tags a capitalized verb as a proper noun.
ACTION_VERBS = set("""
accelerate achieve administer analyze apply architect assess audit automate build calculate
collaborate collect configure consolidate coordinate create cut debug decrease define deliver
deploy design detect develop diagnose direct document drive eliminate enable engineer
escalate establish evaluate execute expand extract facilitate forecast generate grow guide
identify implement improve increase install integrate interview investigate launch lead
maintain manage measure mentor migrate model monitor negotiate optimize orchestrate organize
own partner patch pilot plan present prioritize process produce program propose prototype
provision publish reduce refactor remediate reorganize research resolve restore revamp
scale schedule score secure serve ship simplify solve spearhead standardize streamline
strengthen supervise support test train transform translate triage troubleshoot upgrade
validate visualize win write
""".split())
IRREGULAR_ACTION_FORMS = {"troubleshot", "led", "built", "wrote", "drove", "ran", "won", "grew",
                          "taught", "oversaw", "cut", "spun", "shipped", "set"}

WEAK_VERBS = {
    "help": ["Supported", "Enabled", "Led"], "assist": ["Supported", "Partnered on", "Enabled"],
    "work": ["Built", "Developed", "Delivered"], "participate": ["Contributed to", "Collaborated on"],
    "do": ["Executed", "Completed", "Delivered"], "make": ["Built", "Created", "Designed"],
    "handle": ["Managed", "Resolved", "Owned"], "use": ["Leveraged", "Applied", "Implemented"],
    "try": ["Tested", "Prototyped", "Evaluated"], "get": ["Secured", "Achieved", "Earned"],
    "be": ["Served as", "Operated as"], "attend": ["Completed", "Trained in"],
    "learn": ["Mastered", "Acquired", "Applied"], "go": ["Advanced", "Progressed"],
}
WEAK_OPENINGS = {
    "responsible for": "Owned", "duties included": "Performed", "tasked with": "Delivered",
    "in charge of": "Led", "involved in": "Contributed to", "worked on": "Built",
    "helped with": "Supported", "helped to": "Helped", "assisted with": "Supported",
    "was part of": "Contributed to", "had to": "",
}
FILLER = {"various", "several", "successfully", "effectively", "very", "really", "basically",
          "things", "stuff", "etc", "multiple", "numerous", "actively", "diligently", "hard-working",
          "detail-oriented", "team player", "go-getter", "synergy", "utilize", "utilized"}
PRONOUNS = {"i", "me", "my", "we", "our", "us"}
QUANT_WORDS = {"half", "twice", "double", "doubled", "triple", "tripled", "first", "second", "third",
               "top", "dozen", "dozens", "hundreds", "thousands", "millions"}


def is_quantified(doc) -> bool:
    """Numbers that measure something. Skips version-like numbers in product names
    ("Microsoft 365", "Windows 11") by ignoring numbers right after a proper noun."""
    for t in doc:
        if t.text in ("%", "$") or t.lower_ in QUANT_WORDS:
            return True
        if t.like_num:
            prev = doc[t.i - 1] if t.i > 0 else None
            if prev is not None and prev.pos_ == "PROPN" and prev.text[:1].isupper() and t.text.isdigit():
                continue
            return True
    return False


@dataclass
class BulletReport:
    text: str
    section: str = ""
    score: int = 100
    opening_verb: str = ""
    strong_opening: bool = True
    passive: bool = False
    quantified: bool = False
    filler: list = field(default_factory=list)
    pronouns: list = field(default_factory=list)
    words: int = 0
    issues: list = field(default_factory=list)
    suggestion: str = ""


def is_passive(doc) -> bool:
    return any(t.dep_ in ("nsubjpass", "auxpass", "csubjpass") for t in doc)


def opening(doc) -> tuple[str, bool, str]:
    """Return (first word, is it a strong opening?, suggested replacement)."""
    tokens = [t for t in doc if not t.is_punct and not t.is_space]
    if not tokens:
        return "", False, ""
    first = tokens[0]
    lower = doc.text.lower()
    for phrase, repl in WEAK_OPENINGS.items():
        if lower.startswith(phrase):
            return phrase, False, repl
    lemma = first.lemma_.lower()
    if lemma in WEAK_VERBS:
        return first.text, False, " / ".join(WEAK_VERBS[lemma])
    if first.text.lower() in PRONOUNS:
        return first.text, False, "start with a past-tense action verb"
    # Small models often tag a capitalized verb as a proper noun, so check a lexicon of
    # action verbs too, using the lemma of the lowercase form ("Built" -> "build").
    low_lemma = get_nlp()(first.text.lower())[0].lemma_
    in_lexicon = (lemma in ACTION_VERBS or low_lemma in ACTION_VERBS
                  or first.text.lower() in IRREGULAR_ACTION_FORMS)
    is_verb = in_lexicon or (first.pos_ == "VERB" and first.dep_ == "ROOT")
    if first.text.lower() in PRONOUNS:
        return first.text, False, "start with a past-tense action verb"
    return first.text, is_verb, "" if is_verb else "start with an action verb (Built, Led, Automated...)"


def analyze_bullet(text: str, section: str = "") -> BulletReport:
    nlp = get_nlp()
    doc = nlp(text)
    r = BulletReport(text=text, section=section, words=len([t for t in doc if not t.is_punct]))
    r.opening_verb, r.strong_opening, sugg = opening(doc)
    r.passive = is_passive(doc)
    r.quantified = is_quantified(doc)
    lower_tokens = [t.text.lower() for t in doc]
    joined = " ".join(lower_tokens)
    r.filler = sorted({f for f in FILLER if (f in lower_tokens if " " not in f else f in joined)})
    r.pronouns = sorted({t for t in lower_tokens if t in PRONOUNS})

    if not r.strong_opening:
        r.score -= 25
        r.issues.append(f"weak opening “{r.opening_verb}”" + (f" → try {sugg}" if sugg else ""))
    if r.passive:
        r.score -= 20
        r.issues.append("passive voice: say who did it (you), e.g. “Resolved 40 tickets” not “Tickets were resolved”")
    if not r.quantified:
        r.score -= 15
        r.issues.append("no number: add scale or impact (how many, how much, how fast)")
    if r.filler:
        r.score -= 5 * len(r.filler)
        r.issues.append("filler: " + ", ".join(r.filler))
    if r.pronouns:
        r.score -= 10
        r.issues.append("drop pronouns: " + ", ".join(r.pronouns))
    if r.words < 8:
        r.score -= 10
        r.issues.append(f"too short ({r.words} words): add the result or the tools used")
    elif r.words > 32:
        r.score -= 10
        r.issues.append(f"too long ({r.words} words): split or trim")
    r.score = max(0, r.score)
    r.suggestion = rule_based_rewrite(r)
    return r


IRREGULAR_PAST = {"build": "built", "lead": "led", "write": "wrote", "run": "ran", "make": "made",
                  "teach": "taught", "drive": "drove", "set": "set", "cut": "cut", "win": "won",
                  "give": "gave", "take": "took", "begin": "began", "grow": "grew", "do": "did",
                  "get": "got", "keep": "kept", "find": "found", "hold": "held", "bring": "brought"}


def past_tense(lemma: str) -> str:
    """Tiny English past-tense inflector (enough for resume verbs)."""
    lemma = lemma.lower()
    if lemma in IRREGULAR_PAST:
        return IRREGULAR_PAST[lemma]
    if lemma.endswith("e"):
        return lemma + "d"
    if lemma.endswith("y") and lemma[-2:-1] not in "aeiou":
        return lemma[:-1] + "ied"
    if (len(lemma) <= 4 and lemma[-1] not in "aeiouwxy" and lemma[-2] in "aeiou"
            and lemma[-3:-2] not in "aeiou"):
        return lemma + lemma[-1] + "ed"  # stop -> stopped
    return lemma + "ed"


def _active_from_passive(text: str) -> str | None:
    """'The tickets were resolved by me within SLA' -> 'Resolved the tickets within SLA'."""
    doc = get_nlp()(text)
    root = next((t for t in doc if t.dep_ == "ROOT"), None)
    subj = next((t for t in doc if t.dep_ == "nsubjpass" and t.head == root), None)
    if root is None or subj is None:
        return None
    agent = next((t for t in root.children if t.dep_ == "agent"), None)
    if agent is not None and not any(w.lower_ in PRONOUNS for w in agent.subtree):
        return None  # done by someone else; leave it
    drop = set(range(subj.left_edge.i, subj.right_edge.i + 1))
    drop |= {t.i for t in root.children if t.dep_ == "auxpass" or t.dep_ == "aux"}
    if agent is not None:
        drop |= set(range(agent.left_edge.i, agent.right_edge.i + 1))
    obj = doc[subj.left_edge.i: subj.right_edge.i + 1].text
    rest = " ".join(t.text_with_ws.strip() if t.is_punct else t.text for t in doc
                    if t.i > root.i and t.i not in drop)
    rest = re.sub(r"\s+([.,;:])", r"\1", rest)
    verb = past_tense(root.lemma_).capitalize()
    obj = obj[0].lower() + obj[1:] if obj and not obj.split()[0].isupper() else obj
    return f"{verb} {obj} {rest}".strip()


def rule_based_rewrite(r: BulletReport) -> str:
    """Deterministic fix-ups using the parse: passive -> active, weak opening -> strong
    verb ("Responsible for managing X" -> "Managed X"), strip pronouns and filler.
    (rewrite.py can do fuller rewrites with an LLM.)"""
    text = re.sub(r"^(I|We)\s+", "", r.text.strip())
    if r.passive:
        text = _active_from_passive(text) or text
    nlp = get_nlp()
    lower = text.lower()
    for phrase, repl in WEAK_OPENINGS.items():
        if lower.startswith(phrase):
            rest_doc = nlp(text[len(phrase):].strip())
            if len(rest_doc) and rest_doc[0].tag_ == "VBG":   # "...for managing X"
                text = past_tense(rest_doc[0].lemma_).capitalize() + rest_doc.text[len(rest_doc[0].text):]
            elif repl:
                text = repl + text[len(phrase):]
            break
    else:
        doc = nlp(text)
        if len(doc) and doc[0].lemma_.lower() in WEAK_VERBS:
            repl = WEAK_VERBS[doc[0].lemma_.lower()][0]
            rest = text[len(doc[0].text):]
            # "Participated in X" -> "Contributed to X", not "Contributed to in X"
            if len(repl.split()) > 1 and len(doc) > 1 and doc[1].pos_ == "ADP":
                rest = text[doc[1].idx + len(doc[1].text):]
            text = repl + rest
    for f in r.filler:
        text = re.sub(rf"\b{re.escape(f)}\b\s?", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    if not r.quantified:
        text = text.rstrip(".") + " [+ add a number: scale, %, time saved]."
    return text[0].upper() + text[1:] if text else text


def analyze_bullets(bullets: list[dict]) -> list[BulletReport]:
    return [analyze_bullet(b["text"], b.get("section", "")) for b in bullets]
