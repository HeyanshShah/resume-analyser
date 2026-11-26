# AI Resume Analyzer

An NLP tool that scores how well a resume matches a job description and shows which
ATS (applicant tracking system) keywords are missing.

![screenshot](docs/screenshot.png)

## What it does
1. **Extracts text** from a PDF resume with **PDFMiner**.
2. **Finds skills** in both documents with **spaCy** (`PhraseMatcher` over a curated
   skills list, plus noun-chunk extraction for role-specific phrases).
3. **Measures meaning, not just words**: both texts are turned into
   **sentence embeddings** (`all-MiniLM-L6-v2` via sentence-transformers) and compared
   with **cosine similarity**. Falls back to TF-IDF if the model isn't available.
4. **Scores** the match (60% keyword coverage + 40% semantic similarity) and generates
   feedback: missing skills, repeated phrases you never use, and your most relevant lines.
5. Shows everything in a **Streamlit** web app.

## Tech stack
Python · Streamlit · PDFMiner · spaCy · sentence-transformers · scikit-learn · NumPy · pytest

## Run it
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run app.py
```
Open http://localhost:8501, upload `sample_data/sample_resume.pdf`, and paste
`sample_data/job_description.txt`.

## Deploy
Includes `render.yaml` for one-click deploy on Render (free tier uses the TF-IDF fallback).

## Tests
```bash
pytest
```

## Project layout
```
app.py                 Streamlit UI
analyzer/extract.py    PDF/TXT -> clean text (PDFMiner)
analyzer/keywords.py   skill + phrase extraction (spaCy)
analyzer/similarity.py embeddings + cosine similarity (TF-IDF fallback)
analyzer/scoring.py    combined score + feedback
analyzer/skills.txt    skills dictionary (edit to add more)
tests/                 pytest unit tests
```

## Ideas for next steps
- Suggest rewritten bullets using an LLM
- Support .docx resumes
- Weight "required" skills higher than "nice to have"
