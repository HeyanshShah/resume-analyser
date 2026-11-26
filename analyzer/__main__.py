"""Command line:  python -m analyzer resume.pdf job.txt [--json report.json]"""
import argparse
from dataclasses import asdict
import json
import sys
from pathlib import Path

from .extract import extract_text
from .scoring import analyze


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="analyzer", description="Score a resume against a job posting.")
    p.add_argument("resume")
    p.add_argument("job", help="text file with the job description")
    p.add_argument("--json", help="save the full report as JSON")
    a = p.parse_args(argv)
    resume = extract_text(Path(a.resume).read_bytes(), a.resume)
    r = analyze(resume, Path(a.job).read_text(encoding="utf-8"))
    print(f"MATCH SCORE {r.score}/100   keywords {r.keyword_coverage:.0%} · semantic {r.semantic:.0%} "
          f"· bullet quality {r.bullet_quality:.0%} ({r.method})\n")
    for tip in r.feedback:
        print(" •", tip)
    weakest = sorted(r.bullets, key=lambda b: b.score)[:5]
    if weakest:
        print("\nWeakest bullets:")
        for b in weakest:
            print(f"  [{b.score:3}] {b.text[:90]}")
            for issue in b.issues:
                print(f"        - {issue}")
            print(f"        → {b.suggestion}")
    if a.json:
        out = {"score": r.score, "keyword_coverage": r.keyword_coverage, "semantic": r.semantic,
               "bullet_quality": r.bullet_quality, "keywords": r.keywords,
               "bullets": [asdict(b) for b in r.bullets], "feedback": r.feedback}
        Path(a.json).write_text(json.dumps(out, indent=2))
        print(f"\nSaved {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
