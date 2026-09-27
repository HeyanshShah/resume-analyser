from pathlib import Path

from flask import Flask, Response, render_template_string, request

from resume_analyzer import extract_text_from_file, score_resume

app = Flask(__name__)


def build_report(resume_text: str, job_text: str):
    summary, score = score_resume(resume_text, job_text)
    recommendation = "Strong match" if score >= 80 else "Good potential" if score >= 60 else "Needs improvement"
    lines = [
        "Resume Analysis Report",
        "======================",
        f"Match score: {score}%",
        f"Coverage: {summary['coverage']}",
        f"Recommendation: {recommendation}",
        "",
        "Matched skills:",
    ]
    lines.extend(f"- {skill}" for skill in summary["matched_skills"]) or lines
    lines.extend(["", "Missing skills:"])
    lines.extend(f"- {skill}" for skill in summary["missing_skills"]) or lines
    return "\n".join(lines) + "\n"


HTML = """
<!doctype html>
<html>
  <head>
    <title>Resume Analyzer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      :root {
        --bg-1: #061426;
        --bg-2: #0f172a;
        --card: rgba(15, 23, 42, 0.72);
        --line: rgba(148, 163, 184, 0.2);
        --text: #e2e8f0;
        --muted: #94a3b8;
        --primary: #7c3aed;
        --primary-2: #22c55e;
        --primary-3: #38bdf8;
        --warning: #f59e0b;
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        background: radial-gradient(circle at top, rgba(124,58,237,0.35), transparent 30%),
                    linear-gradient(135deg, var(--bg-1), var(--bg-2));
        color: var(--text);
      }
      .container {
        max-width: 1100px;
        margin: 0 auto;
        padding: 40px 20px 60px;
      }
      .hero {
        display: flex;
        justify-content: space-between;
        align-items: end;
        gap: 20px;
        margin-bottom: 24px;
      }
      h1 {
        margin: 0;
        font-size: clamp(2.2rem, 5vw, 3.6rem);
        letter-spacing: -0.05em;
      }
      .subtitle {
        color: var(--muted);
        margin-top: 10px;
      }
      .panel {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 22px;
        backdrop-filter: blur(12px);
        padding: 28px;
        box-shadow: 0 18px 40px rgba(2, 6, 23, 0.4);
      }
      .panel-glow {
        position: relative;
        overflow: hidden;
      }
      .panel-glow::before {
        content: "";
        position: absolute;
        inset: -30% auto auto -15%;
        width: 220px;
        height: 220px;
        background: radial-gradient(circle, rgba(124, 58, 237, 0.25), transparent 60%);
        pointer-events: none;
      }
      form { display: grid; gap: 18px; }
      label {
        font-size: 0.92rem;
        color: var(--muted);
        font-weight: 600;
        letter-spacing: 0.02em;
      }
      textarea, input[type="file"] {
        width: 100%;
        padding: 14px 16px;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        background: rgba(15, 23, 42, 0.65);
        color: var(--text);
        outline: none;
      }
      textarea {
        min-height: 180px;
        resize: vertical;
      }
      input[type="file"] {
        background: rgba(15, 23, 42, 0.45);
      }
      .actions {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 8px;
      }
      button, .download-btn {
        background: linear-gradient(135deg, var(--primary), #4f46e5);
        color: white;
        padding: 13px 22px;
        border: none;
        border-radius: 12px;
        cursor: pointer;
        font-weight: 700;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 12px 30px rgba(124,58,237,0.35);
      }
      button:hover, .download-btn:hover {
        transform: translateY(-1px);
      }
      .result {
        margin-top: 28px;
      }
      .score {
        font-size: clamp(2rem, 4vw, 3rem);
        font-weight: 800;
        color: #c4b5fd;
        letter-spacing: -0.05em;
      }
      .meta {
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
        margin-top: 14px;
        color: var(--muted);
        font-size: 0.95rem;
      }
      .badge {
        display: inline-block;
        margin-top: 16px;
        padding: 8px 14px;
        background: rgba(34,197,94,0.1);
        color: #86efac;
        border: 1px solid rgba(34,197,94,0.25);
        border-radius: 999px;
        font-weight: 700;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 18px;
        margin-top: 20px;
      }
      .list-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 18px;
      }
      h3 {
        margin-top: 0;
        color: #f8fafc;
      }
      ul {
        margin: 0;
        padding-left: 18px;
        color: var(--text);
        line-height: 1.8;
      }
      .warning {
        margin-top: 20px;
        color: #fcd34d;
        background: rgba(245, 158, 11, 0.08);
        border-left: 4px solid var(--warning);
        padding: 12px 14px;
        border-radius: 10px;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="hero">
        <div>
          <h1>Resume Analyzer</h1>
          <div class="subtitle">AI-style match scoring for resumes and job descriptions</div>
        </div>
      </div>

      <div class="panel panel-glow">
        <form method="post" enctype="multipart/form-data">
          <div>
            <label>Upload resume file</label>
            <input type="file" name="resume_file" accept=".txt,.md,.rtf,.pdf,.doc,.docx">
          </div>

          <div>
            <label>Resume text</label>
            <textarea name="resume" rows="10" placeholder="Paste resume content here">{{ resume_text }}</textarea>
          </div>

          <div>
            <label>Job description</label>
            <textarea name="job" rows="10" placeholder="Paste job description here">{{ job_text }}</textarea>
          </div>

          <div class="actions">
            <button type="submit">Analyze</button>
          </div>
        </form>
      </div>

      {% if result %}
        <div class="result panel panel-glow">
          <div class="score">{{ result.score }}%</div>
          <div class="badge">{{ result.recommendation }}</div>
          <div class="meta">
            <span>Coverage: {{ result.coverage }}</span>
            <span>Matched skills: {{ result.matched_count }}</span>
            <span>Missing skills: {{ result.missing_count }}</span>
          </div>

          <div class="grid">
            <div class="list-card">
              <h3>Matched skills</h3>
              <ul>
                {% for skill in result.matched_skills %}
                  <li>{{ skill }}</li>
                {% endfor %}
              </ul>
            </div>

            <div class="list-card">
              <h3>Missing skills</h3>
              <ul>
                {% for skill in result.missing_skills %}
                  <li>{{ skill }}</li>
                {% endfor %}
              </ul>
            </div>
          </div>

          <div class="actions" style="margin-top: 20px;">
            <a class="download-btn" href="/download-report?resume={{ resume_text|urlencode }}&job={{ job_text|urlencode }}">Download report</a>
          </div>
        </div>
      {% endif %}

      {% if error %}
        <div class="warning">{{ error }}</div>
      {% endif %}
    </div>
  </body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    resume_text = ""
    job_text = ""
    result = None
    error = None

    if request.method == 'POST':
        uploaded_file = request.files.get('resume_file')
        if uploaded_file and uploaded_file.filename:
            temp_path = Path('tmp_resume_upload')
            temp_path.parent.mkdir(exist_ok=True)
            uploaded_file.save(temp_path)
            try:
                resume_text = extract_text_from_file(temp_path)
            except Exception as exc:
                error = f"Unable to read uploaded file: {exc}"
                resume_text = ""

        resume_text = request.form.get('resume', resume_text)
        job_text = request.form.get('job', '')

        if resume_text and job_text:
            summary, score = score_resume(resume_text, job_text)
            result = {
                "score": score,
                "coverage": summary["coverage"],
                "matched_skills": summary["matched_skills"],
                "missing_skills": summary["missing_skills"],
                "matched_count": len(summary["matched_skills"]),
                "missing_count": len(summary["missing_skills"]),
                "recommendation": "Strong match" if score >= 80 else "Good potential" if score >= 60 else "Needs improvement",
            }

    return render_template_string(
        HTML,
        resume_text=resume_text,
        job_text=job_text,
        result=result,
        error=error,
    )


@app.route('/download-report')
def download_report():
    resume_text = request.args.get('resume', '')
    job_text = request.args.get('job', '')
    if not resume_text or not job_text:
        return Response("Missing resume or job description.", status=400)

    report = build_report(resume_text, job_text)
    return Response(
        report,
        mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=resume_analysis_report.txt'}
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
