import json
from pathlib import Path

import pytest

from analyzer.bullets import _active_from_passive, analyze_bullet, past_tense
from analyzer.extract import clean_text, extract_bullets
from analyzer.keywords import find_skills, keyword_coverage
from analyzer.requirements import classify_lines
from analyzer.scoring import analyze
from analyzer.similarity import merge_wrapped_lines, split_chunks

JD = """IT Support Intern
Responsibilities
- Troubleshoot Windows and macOS laptops and resolve tickets in ServiceNow
Requirements
- Must know Active Directory and DNS
Nice to have
- Intune or Jamf experience is a plus"""

RESUME = """EXPERIENCE
IT Service Desk Assistant — Example University
- Resolved 40+ tickets per week in ServiceNow for Windows and macOS users.
- Reset passwords and MFA in Active Directory for 2,000 students.
- Responsible for documentation.
SKILLS
Python, Jamf, DNS"""


# --- skills & synonyms ---
def test_aliases_map_to_canonical_skill():
    assert {"JavaScript", "Kubernetes", "PostgreSQL", "help desk"} <= find_skills(
        "JS, k8s, Postgres, helpdesk")


def test_lemma_matching_handles_word_forms():
    assert "troubleshooting" in find_skills("I troubleshoot and troubleshot printers")


def test_short_names_are_case_sensitive():
    assert "Go" not in find_skills("ready to go fast")
    assert "Go" in find_skills("Backend services in Go and Python")


def test_required_vs_preferred_detection():
    imp = dict(classify_lines(JD))
    assert imp["Must know Active Directory and DNS"] == "required"
    assert imp["Intune or Jamf experience is a plus"] == "preferred"


def test_mixed_paragraph_is_split_into_sentences():
    jd = "Build apps in React and Node.js. Docker experience is a plus. You must know SQL."
    imp = {s: i for s, i in classify_lines(jd)}
    assert list(imp.values()) == ["general", "preferred", "required"]


def test_partial_credit_for_substitute_skill():
    kw = keyword_coverage("Jamf, Active Directory", "Requirements:\nMust know Intune and Active Directory")
    assert [p["skill"] for p in kw["partial"]] == ["Intune"]
    assert 0.5 < kw["coverage"] < 1.0


def test_required_missing_is_reported():
    kw = keyword_coverage("Python only", JD)
    assert {"Active Directory", "DNS"} <= set(kw["required_missing"])


# --- bullet linguistics ---
@pytest.mark.parametrize("text,passive,weak,num", [
    ("Resolved 40 tickets a week for 300 users.", False, False, True),
    ("Tickets were resolved by me within SLA.", True, True, False),
    ("Responsible for managing the help desk queue.", False, True, False),
    ("Helped customers with laptops.", False, True, False),
    ("Configured Microsoft 365 accounts for staff.", False, False, False),  # 365 isn't a metric
    ("Cut response time in half by automating triage.", False, False, True),
])
def test_bullet_checks(text, passive, weak, num):
    r = analyze_bullet(text)
    assert (r.passive, not r.strong_opening, r.quantified) == (passive, weak, num)


def test_passive_to_active_rewrite():
    assert _active_from_passive("The tickets were resolved by me within the SLA.").startswith(
        "Resolved the tickets within the SLA")


def test_weak_opening_rewrite_uses_gerund():
    assert analyze_bullet("Responsible for managing the queue.").suggestion.startswith("Managed the queue")


def test_past_tense():
    assert [past_tense(v) for v in ["build", "automate", "deploy", "stop", "lead", "apply"]] == \
        ["built", "automated", "deployed", "stopped", "led", "applied"]


def test_held_out_accuracy_floor():
    """Linguistic detectors must stay accurate on the held-out labeled set."""
    rows = [json.loads(l) for l in open(Path(__file__).parents[1] / "eval" / "test_set.jsonl")]
    reps = [analyze_bullet(r["text"]) for r in rows]
    acc = lambda pairs: sum(a == b for a, b in pairs) / len(pairs)  # noqa: E731
    assert acc([(x.passive, r["passive"]) for x, r in zip(reps, rows)]) >= 0.9
    assert acc([(not x.strong_opening, r["weak"]) for x, r in zip(reps, rows)]) >= 0.9


# --- extraction ---
def test_extract_bullets_skips_titles_and_merges_wraps():
    text = ("PROJECTS\nProfMatch: Mobile App | React Native\nSep 2024 – Dec 2024\n"
            "Built a mobile app that lets students search and\nreview professors.\n"
            "EXPERIENCE\nIT Assistant — SJSU, San Jose, CA\nDiagnosed Wi-Fi issues for 50 users weekly.")
    bs = extract_bullets(text)
    assert [b["text"] for b in bs] == ["Built a mobile app that lets students search and review professors.",
                                       "Diagnosed Wi-Fi issues for 50 users weekly."]


def test_clean_text_removes_bullets_and_blank_lines():
    assert clean_text("• one\n\n\n  two") == "one\ntwo"


def test_merge_wrapped_lines():
    assert merge_wrapped_lines("Built a tool that\nscans logs.\nNext bullet") == [
        "Built a tool that scans logs.", "Next bullet"]


def test_split_chunks():
    assert len(split_chunks(" ".join(["word"] * 130), max_words=60)) == 3


# --- end to end ---
def test_good_resume_beats_unrelated_one():
    good = analyze(RESUME, JD)
    bad = analyze("EXPERIENCE\nLine cook\n- Prepared meals and cleaned kitchen equipment nightly.", JD)
    assert good.score > bad.score + 25
    assert any("REQUIRED" in t for t in bad.feedback)
