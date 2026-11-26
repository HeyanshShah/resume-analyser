"""Streamlit web interface. Run with:  streamlit run app.py"""
import streamlit as st

from analyzer.extract import extract_text
from analyzer.scoring import analyze

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.title("📄 AI Resume Analyzer")
st.caption("Upload a resume and paste a job description to see your ATS match score "
           "and which keywords you're missing.")

left, right = st.columns(2)
with left:
    upload = st.file_uploader("Resume (.pdf or .txt)", type=["pdf", "txt"])
with right:
    jd_text = st.text_area("Job description", height=260,
                           placeholder="Paste the full job posting here...")

if st.button("Analyze", type="primary", disabled=not (upload and jd_text.strip())):
    try:
        resume_text = extract_text(upload.getvalue(), upload.name)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    if len(resume_text) < 50:
        st.error("Couldn't read much text from that file. Is it a scanned image?")
        st.stop()

    with st.spinner("Analyzing..."):
        r = analyze(resume_text, jd_text)

    a, b, c = st.columns(3)
    a.metric("Match score", f"{r.score}/100")
    b.metric("Keyword coverage", f"{r.keyword_coverage:.0%}")
    c.metric("Semantic similarity", f"{r.semantic:.0%}",
             help=f"Method: {r.method}")
    st.progress(r.score / 100)

    st.subheader("Feedback")
    for tip in r.feedback:
        st.write("• " + tip)

    k1, k2 = st.columns(2)
    with k1:
        st.subheader(f"✅ Matched ({len(r.matched)})")
        st.write(", ".join(r.matched) or "None")
    with k2:
        st.subheader(f"❌ Missing ({len(r.missing)})")
        st.write(", ".join(r.missing) or "None — nice!")

    if r.strongest_lines:
        st.subheader("Your most relevant lines")
        for line, s in r.strongest_lines:
            st.write(f"**{s:.2f}** — {line}")

    with st.expander("Extracted resume text"):
        st.text(resume_text)
