from resume_analyzer.analyzer import extract_keywords, score_resume, extract_text_from_file


def test_extract_keywords_keeps_relevant_terms():
    text = "Python Flask SQL REST APIs Docker leadership project management"

    keywords = extract_keywords(text)

    assert "python" in keywords
    assert "flask" in keywords
    assert "sql" in keywords
    assert "docker" in keywords
    assert "leadership" in keywords


def test_extract_keywords_matches_skill_boundaries_and_api_plural():
    keywords = extract_keywords("NoSQL systems and REST APIs")

    assert "sql" not in keywords
    assert "rest" in keywords
    assert "api" in keywords
    assert "apis" not in keywords


def test_score_resume_returns_high_match_for_relevant_resume():
    job_description = "Looking for Python developer with Flask, SQL, REST APIs, Docker, and Agile experience"
    resume_text = "Experienced Python developer with Flask services, SQL querying, REST APIs, Docker deployment, and Agile delivery."

    summary, score = score_resume(resume_text, job_description)

    assert score >= 75
    assert "python" in summary["matched_skills"]
    assert "flask" in summary["matched_skills"]
    assert "sql" in summary["matched_skills"]
    assert "rest" in summary["matched_skills"]
    assert "docker" in summary["matched_skills"]


def test_extract_text_from_file_reads_plain_text_file(tmp_path):
    target = tmp_path / "resume.txt"
    target.write_text("Python SQL Flask REST API Docker leadership", encoding="utf-8")

    content = extract_text_from_file(target)

    assert "python" in content.lower()
    assert "flask" in content.lower()
    assert "docker" in content.lower()


def test_score_resume_behaves_like_real_world_ats_match():
    job_description = "We need a backend engineer with Python, Flask, SQL, REST APIs, Docker, and Agile delivery."
    resume_text = "Backend engineer experienced in Python backend services, Flask applications, SQL optimization, REST APIs, Docker orchestration, and Agile delivery."

    summary, score = score_resume(resume_text, job_description)

    assert score >= 80
    assert summary["coverage"] >= 0.7
    assert "python" in summary["matched_skills"]
    assert "flask" in summary["matched_skills"]
    assert "sql" in summary["matched_skills"]
    assert "rest" in summary["matched_skills"]
    assert "docker" in summary["matched_skills"]
