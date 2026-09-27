# Resume Analyzer

A lightweight Python utility for comparing a resume against a job description and assigning a relevance score.

## Features

- Extracts likely keywords from resume text and job descriptions
- Matches skills between the two texts
- Produces a simple match percentage score
- Includes a small test suite

## Usage

```python
from resume_analyzer import score_resume

summary, score = score_resume(
    "Experienced Python developer with Flask, SQL, REST APIs, and Docker.",
    "Looking for Python, Flask, SQL, REST APIs, Docker, and Agile experience."
)

print(score)
print(summary)
```

## Web app

Start the browser version:

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

The app accepts resume uploads in plain text and common document formats such as PDF and DOCX.

## Run tests

```bash
pytest
```
