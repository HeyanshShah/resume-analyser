from analyzer.extract import clean_text
from analyzer.keywords import find_skills, keyword_coverage
from analyzer.scoring import analyze
from analyzer.similarity import split_chunks

JD = """We are hiring an IT Support Intern. You will troubleshoot Windows and macOS,
manage Active Directory accounts, reset MFA, and handle tickets in ServiceNow.
Python or PowerShell scripting is a plus. Knowledge of DNS and VPN required."""

GOOD = """IT Service Desk Assistant. Troubleshoot Windows and macOS laptops, manage
Active Directory accounts and MFA resets, resolve tickets in ServiceNow, diagnose DNS
and VPN issues, and automate tasks with PowerShell and Python."""

BAD = """Line cook. Prepared meals, cleaned kitchen equipment, and trained new staff
on food safety procedures during busy dinner shifts."""


def test_find_skills_is_case_insensitive_and_canonical():
    assert {"Python", "Node.js", "Active Directory"} <= find_skills(
        "python, NODE.JS and active directory")


def test_multiword_skill_not_split():
    skills = find_skills("Experience with machine learning")
    assert "machine learning" in skills


def test_coverage_counts_missing():
    kw = keyword_coverage("I know Python.", "Need Python and SQL.")
    assert kw["matched"] == ["Python"]
    assert kw["missing"] == ["SQL"]
    assert kw["coverage"] == 0.5


def test_good_resume_beats_bad_resume():
    good, bad = analyze(GOOD, JD), analyze(BAD, JD)
    assert good.score > bad.score
    assert good.score >= 60
    assert bad.score < 30


def test_clean_text_removes_bullets_and_blank_lines():
    assert clean_text("• one\n\n\n  two") == "one\ntwo"


def test_split_chunks():
    text = " ".join(["word"] * 130)
    assert len(split_chunks(text, max_words=60)) == 3


def test_merge_wrapped_lines():
    from analyzer.similarity import merge_wrapped_lines
    assert merge_wrapped_lines("Built a tool that\nscans logs.\nNext bullet") == [
        "Built a tool that scans logs.", "Next bullet"]
