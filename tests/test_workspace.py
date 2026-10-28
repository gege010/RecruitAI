import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from core.mcdm.ahp import compute_ahp
from core.mcdm.saw import run_saw
from core.mcdm.topsis import run_topsis
from core.mcdm.weighted_product import run_wp
from server.main import app, LOGIN_ATTEMPTS
from server.models import JobInput
from server.scoring import dimensions

HEADERS = {"X-RecruitAI-Request": "1"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RECRUITAI_DB", str(tmp_path / "test.sqlite3"))
    monkeypatch.delenv("RECRUITAI_PASSWORD", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    LOGIN_ATTEMPTS.clear()
    with TestClient(app, headers=HEADERS) as c:
        yield c


def job(client):
    response = client.post(
        "/api/jobs",
        json={"title": "Software Engineer", "required_skills": ["Python", "SQL"]},
    )
    assert response.status_code == 201
    return response.json()


def profile(name="Test Candidate", **kw):
    return {
        "name": name,
        "skills": ["Python", "SQL"],
        "experience_months": 36,
        "education": "S1",
        "languages": ["Indonesia"],
        **kw,
    }


def add(client, jid, **kw):
    r = client.post(f"/api/jobs/{jid}/candidates", json=profile(**kw))
    assert r.status_code == 201
    return r.json()["id"]


def test_full_selection_and_snapshot(client):
    j = job(client)
    first = add(client, j["id"], name="Qualified")
    add(client, j["id"], name="Needs review", skills=["SQL"], experience_months=None)
    result = client.post(f"/api/jobs/{j['id']}/analyze")
    assert result.status_code == 200
    listing = client.get(f"/api/jobs/{j['id']}/candidates").json()
    assert listing["items"][0]["id"] == first
    assert listing["items"][0]["result"]["score"] == 100
    assert not listing["stale"]
    c = listing["items"][0]
    r = client.patch(
        "/api/candidates/" + c["id"],
        json={"status": "shortlisted", "note": "Bukti sesuai", "version": c["version"]},
    )
    assert r.status_code == 200
    stale_edit = client.patch(
        "/api/candidates/" + c["id"], json={"status": "hold", "version": c["version"]}
    )
    assert stale_edit.status_code == 409
    export = client.get(f"/api/jobs/{j['id']}/export")
    assert export.status_code == 200
    assert "Qualified" in export.text
    assert result.json()["id"] in export.text
    add(client, j["id"], name="New arrival")
    assert client.get(f"/api/jobs/{j['id']}/candidates").json()["stale"]


def test_profile_correction_invalidates_analysis(client):
    j = job(client)
    cid = add(client, j["id"])
    add(client, j["id"], name="Second")
    client.post(f"/api/jobs/{j['id']}/analyze")
    assert (
        client.put(
            "/api/candidates/" + cid + "/profile?version=1",
            json=profile(experience_months=12),
        ).status_code
        == 200
    )
    assert client.get(f"/api/jobs/{j['id']}/candidates").json()["stale"]
    assert (
        client.put(
            "/api/candidates/" + cid + "/profile?version=1", json=profile()
        ).status_code
        == 409
    )


def test_validation_and_job_concurrency(client):
    assert (
        client.post(
            "/api/jobs", json={"title": "   ", "required_skills": ["Python"]}
        ).status_code
        == 422
    )
    j = job(client)
    assert (
        client.put(
            "/api/jobs/" + j["id"], json={**j, "title": "Updated Engineer"}
        ).status_code
        == 200
    )
    assert client.put("/api/jobs/" + j["id"], json=j).status_code == 409
    assert client.post(f"/api/jobs/{j['id']}/analyze").status_code == 422
    cid = add(client, j["id"])
    assert (
        client.patch(
            "/api/candidates/" + cid, json={"status": "rejected", "version": 1}
        ).status_code
        == 422
    )
    assert client.get(f"/api/jobs/{j['id']}/candidates?page=0").status_code == 422
    assert client.get("/api/jobs/no-such-job/candidates").status_code == 404


def test_auth_csrf_and_logout(client, monkeypatch):
    monkeypatch.setenv("RECRUITAI_PASSWORD", "a-long-workspace-password")
    assert client.get("/api/jobs").status_code == 401
    assert client.post("/api/login", json={"password": "wrong"}).status_code == 401
    assert (
        client.post(
            "/api/login",
            json={"password": "a-long-workspace-password"},
            headers={"origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/login", json={"password": "a-long-workspace-password"}
        ).status_code
        == 200
    )
    assert client.get("/api/jobs").status_code == 200
    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/jobs").status_code == 401


def test_csrf_header_required(client):
    response = client.post("/api/demo", headers={"X-RecruitAI-Request": ""})
    assert response.status_code == 403


def test_demo_explicit_and_only_empty_workspace(client):
    assert client.get("/api/jobs").json() == []
    assert client.post("/api/demo").status_code == 201
    assert client.post("/api/demo").status_code == 409
    j = client.get("/api/jobs").json()[0]
    assert j["candidate_count"] == 6


def test_search_pagination_and_status(client):
    j = job(client)
    for n in range(12):
        add(client, j["id"], name=f"Candidate {n}")
    d = client.get(f"/api/jobs/{j['id']}/candidates?page=999").json()
    assert d["page"] == 2 and len(d["items"]) == 2
    d = client.get(f"/api/jobs/{j['id']}/candidates?q=Candidate%2011").json()
    assert d["total"] == 1
    assert (
        client.get(f"/api/jobs/{j['id']}/candidates?status=shortlisted").json()["total"]
        == 0
    )


def test_pdf_limits_and_duplicates(client, monkeypatch):
    from server import extraction

    j = job(client)
    assert (
        client.post(
            f"/api/jobs/{j['id']}/upload", files={"file": ("evil.pdf", b"not-pdf")}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/jobs/{j['id']}/upload",
            files={"file": ("big.pdf", b"%PDF-" + b"x" * (10 * 1024 * 1024))},
        ).status_code
        == 413
    )
    monkeypatch.setattr(extraction, "extract", lambda *args: (profile(), "local"))
    pdf = b"%PDF-1.7\nmock-valid-content"
    assert (
        client.post(
            f"/api/jobs/{j['id']}/upload", files={"file": ("resume.pdf", pdf)}
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/api/jobs/{j['id']}/upload", files={"file": ("other-name.pdf", pdf)}
        ).status_code
        == 409
    )


def test_csv_formula_injection(client):
    j = job(client)
    add(client, j["id"], name='=HYPERLINK("evil")')
    add(client, j["id"], name="Normal")
    client.post(f"/api/jobs/{j['id']}/analyze")
    assert "'=HYPERLINK" in client.get(f"/api/jobs/{j['id']}/export").text


def test_missing_evidence_and_meeting_requirement():
    j = JobInput(title="Engineer", required_skills=["Python"]).model_dump()
    scores, evidence = dimensions(profile(), j)
    assert scores["experience"] == 1.0
    assert scores["skills"] == 1.0
    scores, evidence = dimensions(profile(experience_months=None, education=""), j)
    assert scores["experience"] == 0
    assert len(evidence["unknown"]) == 2


@pytest.mark.parametrize("method", [run_saw, run_wp, run_topsis])
def test_mcdm_invariants(method):
    matrix = pd.DataFrame([[1, 1], [0.3, 0.4]], index=["a", "b"])
    result = method(matrix, [0.5, 0.5])
    assert result["a"] > result["b"]
    assert np.isfinite(result).all()
    for weights in [[0, 0], [-1, 2], [float("nan"), 1], [1]]:
        with pytest.raises(ValueError):
            method(matrix, weights)
    with pytest.raises(ValueError):
        method(pd.DataFrame([[float("inf"), 1]]), [0.5, 0.5])


def test_ties_and_ahp():
    result = run_topsis(pd.DataFrame([[0.5, 0.5], [0.5, 0.5]]), [0.5, 0.5])
    assert result.tolist() == [0.5, 0.5]
    assert compute_ahp([[1, 2], [0.5, 1]])["is_valid"]
    for invalid in [
        [],
        [[1, 0], [0, 1]],
        [[1, 2], [2, 1]],
        [[1, float("nan")], [1, 1]],
    ]:
        with pytest.raises(ValueError):
            compute_ahp(invalid)


def test_production_refuses_weak_password(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("RECRUITAI_PASSWORD", "short")
    monkeypatch.setenv("RECRUITAI_DB", str(tmp_path / "secure.sqlite3"))
    with pytest.raises(RuntimeError, match="Production requires"):
        with TestClient(app):
            pass


def test_real_pdf_local_extraction_and_scan_failure():
    import fitz
    from server.extraction import extract

    j = JobInput(title="Engineer", required_skills=["Python", "SQL"]).model_dump()
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Ayu Candidate\nSoftware Engineer\nSkills: Python, SQL\nBachelor of Computer Science\nLanguages: Indonesian, English",
    )
    data = doc.tobytes()
    doc.close()
    parsed, source = extract(data, "resume.pdf", j, False)
    assert source == "local"
    assert parsed["name"] == "Ayu Candidate"
    assert parsed["skills"] == ["Python", "SQL"]
    assert parsed["education"] == "S1"
    assert parsed["experience_months"] is None
    assert parsed["languages"] == ["Indonesia", "Inggris"]
    doc = fitz.open()
    doc.new_page()
    with pytest.raises(ValueError, match="tidak terbaca"):
        extract(doc.tobytes(), "empty.pdf", j, False)
    doc.close()
