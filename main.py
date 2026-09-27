import argparse
import json
from pathlib import Path

from resume_analyzer import score_resume


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Compare a resume against a job description.")
    parser.add_argument("--resume", required=True, help="Path to the resume text file.")
    parser.add_argument("--job-description", required=True, help="Path to the job description text file.")
    args = parser.parse_args()

    resume_text = read_text(args.resume)
    job_text = read_text(args.job_description)
    summary, score = score_resume(resume_text, job_text)

    result = {
        "score": score,
        "matched_skills": summary["matched_skills"],
        "missing_skills": summary["missing_skills"],
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
