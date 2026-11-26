# AI Resume Analyzer: how to explain it (plain English)

## 30-second pitch
"It's a resume analyzer built on computational linguistics, which ties into my CS +
Linguistics degree. Most resume checkers just count keywords. Mine understands synonyms
like JS for JavaScript, matches different word forms using lemmas, and reads the job posting's
wording to tell required skills from nice-to-haves. It also grades every bullet with spaCy's
dependency parser: it detects passive voice, weak openings like 'Responsible for', and bullets
with no measurable impact, then rewrites them automatically. On a held-out test set the
detectors hit 93–97% accuracy with 100% precision."

## Linguistics terms you should be able to explain
- **Lemma:** the dictionary form of a word. troubleshooting / troubleshot → *troubleshoot*. Matching
  on lemmas means different forms of a word still count.
- **Part of speech (POS):** noun, verb, and so on. I check that a bullet starts with a VERB.
- **Dependency parse:** a tree showing how the words in a sentence relate. In "Tickets were resolved,"
  the parser labels *tickets* as `nsubjpass` (passive subject) and *were* as `auxpass`. That's how I
  detect passive voice. It's grammar, not a word list.
- **Passive → active rewrite:** find the verb and its passive subject, drop "were" and "by me", put the verb
  in past tense first, then move the old subject after it: "The tickets were resolved by me" → "Resolved the tickets."
- **Get-passive:** "got certified" is also passive. My evaluation caught that, and it's a good linguistics detail to mention.
- **Embeddings / cosine similarity:** text → 384 numbers that capture meaning; the angle between two of them measures similarity.

## How the score works
50% weighted keywords (what an ATS checks) + 25% meaning similarity + 25% bullet quality (what a human
notices). Required skills count 1.0, unmarked 0.75, preferred 0.5. Substitute skills (MySQL vs.
PostgreSQL, Intune vs. Jamf) get half credit, but languages don't: knowing Java doesn't mean you know Go.

## Why my accuracy numbers are honest (they WILL respect this)
I made two labeled sets. The **dev set** (50 bullets) was used while building, and it scores 100%, but
that's meaningless because I tuned on it. The **test set** (30 bullets) was written afterwards and never
used for tuning: 97% passive, 93% weak-opening, and 97% quantified accuracy, with 100% precision on all
three. When it flags something, it's right. "Separating dev and test sets is basic ML hygiene" is a
great line to say.

## Problems I solved
1. **The small spaCy model tags capitalized verbs as proper nouns** ("Built" → PROPN). I added an
   action-verb lexicon checked against the lemma, plus irregular forms like "Troubleshot" and "Led".
2. **"Microsoft 365" counted as a metric.** I now skip numbers that directly follow a proper noun (product versions).
3. **Single-paragraph job posts** marked every skill as "preferred" because one sentence said "a plus".
   I now judge importance per sentence. A test covers it.
4. **"Participated in X" → "Contributed to in X".** When the new verb carries its own preposition,
   I drop the old one.

## Limits (say these before they ask)
- Rule-based detectors miss some patterns, like subject-less passives and idioms ("Took part in").
- The ontology is hand-built (143 skills), so new tools need adding.
- It's a guide, not a real ATS; every company's ATS differs.

## Commands
`streamlit run app.py` · `python -m analyzer resume.pdf job.txt` · `python eval/evaluate_bullets.py test` · `pytest`
