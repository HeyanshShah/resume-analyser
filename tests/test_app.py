from io import BytesIO
from pathlib import Path

import app as app_module

app = app_module.app


def test_uploaded_resume_is_used_when_textarea_is_empty():
    client = app.test_client()
    response = client.post(
        "/",
        data={
            "resume": "",
            "job": "Python Flask SQL developer",
            "resume_file": (BytesIO(b"Python Flask SQL developer"), "resume.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Matched skills" in response.data
    assert b"python" in response.data
    assert b"No resume text" not in response.data


def test_unsupported_upload_is_rejected():
    client = app.test_client()
    response = client.post(
        "/",
        data={
            "resume": "",
            "job": "Python developer",
            "resume_file": (BytesIO(b"not a document"), "resume.exe"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Unsupported file type" in response.data


def test_uploaded_temporary_file_is_deleted_after_extraction(monkeypatch):
    extracted_paths = []

    def extract_during_test(path):
        path = Path(path)
        assert path.exists()
        extracted_paths.append(path)
        return "Python Flask developer"

    monkeypatch.setattr(app_module, "extract_text_from_file", extract_during_test)
    response = app.test_client().post(
        "/",
        data={
            "resume": "",
            "job": "Python Flask developer",
            "resume_file": (BytesIO(b"resume"), "resume.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert len(extracted_paths) == 1
    assert not extracted_paths[0].exists()


def test_report_download_uses_post_and_does_not_put_resume_in_url():
    client = app.test_client()
    resume = "Private Candidate Name Python"
    response = client.post(
        "/download-report",
        data={"resume": resume, "job": "Python developer"},
    )

    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert b"Private Candidate Name" not in response.data
    assert b"/download-report?" not in client.get("/").data


def test_report_download_rejects_missing_text():
    client = app.test_client()
    response = client.post("/download-report", data={"resume": "", "job": "Python"})

    assert response.status_code == 400
