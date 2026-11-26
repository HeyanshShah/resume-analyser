# AI Resume Analyzer: how to explain it (plain English)

## The 30-second pitch
"I built a tool that tells you how well your resume matches a job posting. You upload a
PDF and paste the job description. It pulls out the skills from both, shows which
keywords you're missing, and uses embeddings to check whether your resume *means* the
same kind of work, not just uses the same words. It gives a score out of 100 and
specific feedback. It's Python, with spaCy for NLP, sentence-transformers for
embeddings, and Streamlit for the web interface."

## How it works, step by step (the 4 files)
1. **extract.py: reading the PDF.** PDFs don't store paragraphs, they store letters at
   positions on a page. PDFMiner rebuilds readable text. Then I clean it up: remove
   bullet symbols and blank lines.
2. **keywords.py: finding skills.** I keep a list of ~150 skills (Python, SQL, Active
   Directory...). spaCy's PhraseMatcher finds them, ignoring capitalization, and it
   keeps multi-word skills together ("machine learning" is one skill, not two words).
   I also use spaCy's noun chunks to catch phrases the posting repeats that aren't in
   my list, like "knowledge base articles".
3. **similarity.py: comparing meaning.** An embedding model turns text into a list of
   384 numbers. Texts that mean similar things get similar numbers. I compare the
   resume's numbers to the job's numbers with cosine similarity: 1 means identical
   direction, 0 means unrelated. Long text gets split into ~60-word chunks first, because
   the model works best on short passages, then I average them.
4. **scoring.py: the final score.** 60% keyword coverage + 40% meaning similarity.
   Keywords get more weight because real ATS filters are mostly keyword-based.

## Why I chose each tool (they WILL ask "why X?")
- **spaCy** over NLTK: faster, has PhraseMatcher and a parser for noun chunks built in.
- **all-MiniLM-L6-v2**: small (~90 MB), fast on a laptop CPU, good quality for
  sentence similarity. A bigger model wasn't worth the speed cost.
- **TF-IDF fallback**: if the model can't download, the app still works. TF-IDF scores
  words by how often they appear in one document vs. how common they are overall.
- **Streamlit**: turns a Python script into a web app without writing HTML/JavaScript.

## A problem I hit (good story for "tell me about a challenge")
"PDF text came out broken: one bullet point would be split across three lines, so when
I showed 'your most relevant lines' it showed half-sentences. I fixed it by detecting
continuation lines (ones starting with a lowercase letter, or following a comma) and
gluing them back together. I wrote a unit test for it so it wouldn't break again."

Another one: "The phrase extractor was returning junk like '500 employees' and
'python requirements' (a skill merged with the next heading). I treated line breaks as
sentence boundaries and filtered out numbers and generic words."

## What I'd improve
- Use an LLM to suggest rewritten bullets, not just list missing words.
- Separate "required" vs "nice to have" skills and weight them differently.
- Support Word (.docx) resumes.

## Likely questions + answers
- **What's an embedding?** A list of numbers representing the meaning of text, so a
  computer can measure how similar two texts are.
- **What's cosine similarity?** The angle between two vectors. Same direction = 1.0.
- **What's NER?** Named-entity recognition: finding names of things (companies,
  products, places) in text. I use spaCy's entities for ORG/PRODUCT names.
- **How did you test it?** pytest unit tests: case-insensitive skill matching,
  multi-word skills, coverage math, a matching resume scoring higher than an unrelated
  one, and the line-merging fix.
- **How accurate is it?** On my test, an IT resume scored 68 against an IT posting and a
  line-cook resume scored 12. It's a guide, not a real ATS, because every company's ATS
  is different.

## Commands to remember
- `streamlit run app.py` runs the app
- `pytest` runs the tests
- `pip install -r requirements.txt` installs everything
