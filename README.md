# Resume Analyzer

A portfolio-ready resume matching tool that compares a resume against a job description and highlights skill alignment, gaps, and estimated keyword coverage.

The score is a transparent keyword-based heuristic, not an AI model or an automated hiring decision. Scanned PDFs require OCR and may not yield extractable text.

## Project Overview

This project was built to simulate a practical hiring workflow: a recruiter or candidate can paste a resume and job description, and the app calculates how well the resume matches the role based on relevant technical skills and keywords.

It is designed as a lightweight, real-world prototype for ATS-style scoring and can be extended into a more advanced hiring analytics tool.

## Key Features

- Resume vs job description matching
- Skill extraction for technical keywords
- Weighted relevance scoring
- Coverage analysis and missing-skill detection
- Resume upload support for text-based formats and common document files
- Clean web interface built with Flask
- Automated tests for scoring reliability

## Tech Stack

- Python
- Flask
- PyPDF2
- python-docx
- Pytest

## Project Structure

```bash
resume-analyzer/
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
├── sample_resume.txt
├── sample_job_description.txt
├── resume_analyzer/
│   ├── __init__.py
│   └── analyzer.py
├── tests/
│   └── test_analyzer.py
└── .gitignore
```

## How It Works

1. The app reads the resume text and job description.
2. It extracts relevant skill keywords and common technical terms.
3. It compares the resume skills against the required job skills.
4. It calculates a match score and shows missing skills.
5. It presents a recruiter-friendly result summary.

## Local Setup

### 1. Clone the project

```bash
git clone https://github.com/HeyanshShah/resume-analyser.git
cd resume-analyser
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Run the app

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

### 4. Run tests

```bash
python -m pytest -q
```

## Sample Usage

```python
from resume_analyzer import score_resume

summary, score = score_resume(
    "Experienced Python developer with Flask, SQL, REST APIs, and Docker.",
    "Looking for Python, Flask, SQL, REST APIs, Docker, and Agile experience."
)

print(score)
print(summary)
```

## Example Output

```json
{
  "score": 75,
  "matched_skills": ["python", "flask", "sql", "docker", "rest"],
  "missing_skills": ["project management"]
}
```

## Screenshots

This project is intended to be used via a browser-based dashboard with:
- resume text input
- file upload support
- score summary
- matched and missing skill lists
- downloadable result report

## Future Enhancements

- Multi-file comparison for multiple candidates
- Better resume parsing using NLP and Named Entity Recognition
- Stronger weighting for experience, education, certifications, and tools
- Deployment to a hosted web app
- CSV export and recruiter dashboard analytics

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

Heyansh Shah
