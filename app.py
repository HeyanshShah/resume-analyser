"""Streamlit web interface. Run with:  streamlit run app.py"""
import json
from dataclasses import asdict

import pandas as pd
import streamlit as st

from analyzer import rewrite
from analyzer.extract import extract_text
from analyzer.scoring import analyze

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.title("📄 AI Resume Analyzer")
st.caption("ATS keyword matching with synonyms and required-vs-preferred weighting, embedding "
           "similarity, and a linguistic grader for every bullet (voice, verbs, impact).")

left, right = st.columns(2)
with left:
    upload = st.file_uploader("Resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
with right:
    jd_text = st.text_area("Job description", height=240, placeholder="Paste the full job posting...")

if st.button("Analyze", type="primary", disabled=not (upload and jd_text.strip())):
    try:
        resume_text = extract_text(upload.getvalue(), upload.name)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    if len(resume_text.strip()) < 50:
        st.error("Couldn't read much text from that file. Is it a scanned image?")
        st.stop()
    with st.spinner("Analyzing..."):
        st.session_state.report = analyze(resume_text, jd_text)
        st.session_state.jd = jd_text

r = st.session_state.get("report")
if r is None:
    st.stop()

c = st.columns(4)
c[0].metric("Match score", f"{r.score}/100")
c[1].metric("Weighted keywords", f"{r.keyword_coverage:.0%}", help="Required skills count 2x preferred")
c[2].metric("Semantic similarity", f"{r.semantic:.0%}", help=f"Method: {r.method}")
c[3].metric("Bullet quality", f"{r.bullet_quality:.0%}")
st.progress(r.score / 100)

tabs = st.tabs(["💡 Feedback", "🧩 Skills", "✍️ Bullet grades", "🔁 Rewrites", "⬇️ Export"])

with tabs[0]:
    for tip in r.feedback:
        st.write("• " + tip)
    if r.strongest_lines:
        st.subheader("Your most relevant lines")
        for line, s in r.strongest_lines:
            st.write(f"**{s:.2f}** · {line}")

with tabs[1]:
    rows = ([{**m, "status": "✅ have"} for m in r.keywords["matched"]] +
            [{**m, "status": f"🟡 similar: {m['you_have']}"} for m in r.keywords["partial"]] +
            [{**m, "status": "❌ missing"} for m in r.keywords["missing"]])
    order = {"required": 0, "general": 1, "preferred": 2}
    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(["importance", "status"], key=lambda s: s.map(order) if s.name == "importance" else s)
        st.dataframe(df[["skill", "importance", "status", "family"]], hide_index=True, use_container_width=True)
    st.caption("Importance comes from the posting's section headers and wording "
               "(\"required\", \"must\" vs. \"a plus\", \"nice to have\").")

with tabs[2]:
    if not r.bullets:
        st.info("No bullets found under Experience / Projects / Activities headings.")
    else:
        bdf = pd.DataFrame([{"score": b.score, "bullet": b.text, "verb": "✅" if b.strong_opening else "⚠️",
                             "active": "⚠️ passive" if b.passive else "✅",
                             "number": "✅" if b.quantified else "—",
                             "issues": "; ".join(b.issues)} for b in r.bullets]).sort_values("score")
        st.dataframe(bdf.style.background_gradient(subset=["score"], cmap="RdYlGn", vmin=40, vmax=100),
                     hide_index=True, use_container_width=True, height=520)

with tabs[3]:
    weak = [b for b in sorted(r.bullets, key=lambda b: b.score) if b.score < 100][:8]
    if not weak:
        st.success("Every bullet passed the checks.")
    use_llm = rewrite.available() and st.toggle("Rewrite with Claude (uses your ANTHROPIC_API_KEY)")
    llm_out = None
    if use_llm and weak:
        with st.spinner("Asking Claude..."):
            try:
                llm_out = rewrite.rewrite_bullets([b.text for b in weak],
                                                  [m["skill"] for m in r.keywords["missing"]][:10])
            except Exception as e:  # network/model errors shouldn't break the app
                st.warning(f"LLM rewrite failed ({e}); showing rule-based rewrites.")
    for i, b in enumerate(weak):
        st.markdown(f"**Before** ({b.score}): {b.text}")
        st.markdown(f"**After:** {llm_out[i] if llm_out else b.suggestion}")
        st.divider()
    if not rewrite.available():
        st.caption("Tip: set ANTHROPIC_API_KEY and `pip install anthropic` for full AI rewrites. "
                   "Rule-based rewrites (passive → active, weak verb → strong verb) work offline.")

with tabs[4]:
    out = {"score": r.score, "keyword_coverage": r.keyword_coverage, "semantic": r.semantic,
           "bullet_quality": r.bullet_quality, "keywords": r.keywords, "feedback": r.feedback,
           "bullets": [asdict(b) for b in r.bullets]}
    st.download_button("Download full report (JSON)", json.dumps(out, indent=2), "resume_report.json")
