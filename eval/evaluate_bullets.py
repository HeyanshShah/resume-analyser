"""Measure the bullet linguistics detectors against 50 hand-labeled resume bullets.

Two sets, kept separate on purpose:
  dev_set.jsonl  - 50 bullets I used while building the rules (scores here are optimistic)
  test_set.jsonl - 30 bullets written afterwards and never used for tuning (the honest number)

Run:  python eval/evaluate_bullets.py [dev|test]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyzer.bullets import analyze_bullet  # noqa: E402

SPLIT = sys.argv[1] if len(sys.argv) > 1 else "test"
rows = [json.loads(l) for l in open(Path(__file__).with_name(f"{SPLIT}_set.jsonl"))]


def metrics(pairs):
    tp = sum(p and t for p, t in pairs)
    fp = sum(p and not t for p, t in pairs)
    fn = sum(t and not p for p, t in pairs)
    acc = sum(p == t for p, t in pairs) / len(pairs)
    prec = tp / (tp + fp) if tp + fp else 1.0
    rec = tp / (tp + fn) if tp + fn else 1.0
    return acc, prec, rec


def run():
    reports = [analyze_bullet(r["text"]) for r in rows]
    checks = {
        "passive voice": [(rep.passive, r["passive"]) for rep, r in zip(reports, rows)],
        "weak opening": [(not rep.strong_opening, r["weak"]) for rep, r in zip(reports, rows)],
        "quantified": [(rep.quantified, r["quantified"]) for rep, r in zip(reports, rows)],
    }
    results = {k: metrics(v) for k, v in checks.items()}
    errors = [(k, r["text"]) for k, v in checks.items() for (p, t), r in zip(v, rows) if p != t]
    return results, errors


if __name__ == "__main__":
    results, errors = run()
    print(f"{SPLIT} set: {len(rows)} hand-labeled bullets\n")
    print("| Detector | Accuracy | Precision | Recall |\n|---|---|---|---|")
    for k, (a, p, r) in results.items():
        print(f"| {k} | {a:.0%} | {p:.0%} | {r:.0%} |")
    if errors:
        print("\nMistakes:")
        for k, t in errors:
            print(f"  [{k}] {t}")
