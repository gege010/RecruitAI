import csv
import hashlib
import hmac
import io
import json
import logging
import os
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from fastapi import FastAPI, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from server import store
from server.models import JobInput, JobUpdate, ProfileInput, ReviewInput, LoginInput
from server.scoring import analyze

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("recruitai")
LOGIN_ATTEMPTS = defaultdict(deque)


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid4())


@asynccontextmanager
async def lifespan(app):
    if (
        os.getenv("APP_ENV") == "production"
        and len(os.getenv("RECRUITAI_PASSWORD", "")) < 16
    ):
        raise RuntimeError(
            "Production requires RECRUITAI_PASSWORD of at least 16 characters."
        )
    store.initialize()
    yield


app = FastAPI(
    title="RecruitAI Workspace",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if os.getenv("APP_ENV") == "production" else "/docs",
)


@app.middleware("http")
async def security(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        expected = os.getenv("RECRUITAI_ORIGIN", str(request.base_url).rstrip("/"))
        if origin and origin != expected:
            return JSONResponse(
                {"detail": "Asal permintaan tidak diizinkan."}, status_code=403
            )
        if (
            request.headers.get("content-length", "0").isdigit()
            and int(request.headers.get("content-length", "0")) > 12 * 1024 * 1024
        ):
            return JSONResponse(
                {"detail": "Permintaan melebihi batas 12 MB."}, status_code=413
            )
        if (
            request.url.path.startswith("/api/")
            and request.headers.get("x-recruitai-request") != "1"
        ):
            return JSONResponse(
                {"detail": "Header keamanan diperlukan."}, status_code=403
            )
    response = await call_next(request)
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "X-Frame-Options": "DENY",
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }
    )
    return response


def authorized(request: Request):
    if not os.getenv("RECRUITAI_PASSWORD"):
        # No authentication is allowed only for development on loopback.
        if os.getenv("APP_ENV") == "production" or request.client.host not in {
            "127.0.0.1",
            "::1",
            "testclient",
        }:
            raise HTTPException(401, "Atur kata sandi untuk akses jaringan.")
        return
    token = request.cookies.get("recruitai_session", "")
    with store.connect() as db:
        session = db.execute(
            "SELECT expires FROM sessions WHERE token_hash=?",
            (hashlib.sha256(token.encode()).hexdigest(),),
        ).fetchone()
    if not session or session["expires"] < time.time():
        raise HTTPException(401, "Sesi berakhir. Silakan masuk kembali.")


def get_job(db, job_id):
    row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Lowongan tidak ditemukan.")
    return store.unpack(row)


@app.get("/health")
def health():
    with store.connect() as db:
        db.execute("SELECT 1")
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/session")
def session(request: Request):
    try:
        authorized(request)
        authenticated = True
    except HTTPException:
        authenticated = False
    return {
        "authenticated": authenticated,
        "password_required": bool(os.getenv("RECRUITAI_PASSWORD")),
        "ai_available": bool(os.getenv("GROQ_API_KEY")),
        "local_only": not bool(os.getenv("RECRUITAI_PASSWORD")),
    }


@app.post("/api/login")
def login(body: LoginInput, request: Request):
    attempts = LOGIN_ATTEMPTS[request.client.host]
    while attempts and attempts[0] < time.time() - 300:
        attempts.popleft()
    if len(attempts) >= 5:
        raise HTTPException(
            429, "Terlalu banyak percobaan. Coba kembali dalam 5 menit."
        )
    password = os.getenv("RECRUITAI_PASSWORD", "")
    if not password or not hmac.compare_digest(
        body.password.encode(), password.encode()
    ):
        attempts.append(time.time())
        raise HTTPException(401, "Kata sandi tidak sesuai.")
    attempts.clear()
    token = secrets.token_urlsafe(48)
    with store.connect() as db:
        db.execute("DELETE FROM sessions WHERE expires<?", (time.time(),))
        db.execute(
            "INSERT INTO sessions VALUES(?,?)",
            (hashlib.sha256(token.encode()).hexdigest(), time.time() + 28800),
        )
    response = JSONResponse({"ok": True})
    response.set_cookie(
        "recruitai_session",
        token,
        httponly=True,
        secure=os.getenv("APP_ENV") == "production",
        samesite="strict",
        max_age=28800,
    )
    return response


@app.post("/api/logout")
def logout(request: Request):
    with store.connect() as db:
        db.execute(
            "DELETE FROM sessions WHERE token_hash=?",
            (
                hashlib.sha256(
                    request.cookies.get("recruitai_session", "").encode()
                ).hexdigest(),
            ),
        )
    response = JSONResponse({"ok": True})
    response.delete_cookie("recruitai_session")
    return response


@app.get("/api/jobs", dependencies=[Depends(authorized)])
def jobs():
    with store.connect() as db:
        items = [
            store.unpack(r)
            for r in db.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        ]
        for item in items:
            item["candidate_count"] = db.execute(
                "SELECT COUNT(*) FROM candidates WHERE job_id=?", (item["id"],)
            ).fetchone()[0]
    return items


@app.post("/api/jobs", status_code=201, dependencies=[Depends(authorized)])
def create_job(body: JobInput):
    job_id, date = uid(), now()
    with store.connect() as db:
        db.execute(
            "INSERT INTO jobs(id,data,created_at) VALUES(?,?,?)",
            (job_id, body.model_dump_json(), date),
        )
        store.audit(db, "Lowongan dibuat", job_id, date)
        return get_job(db, job_id)


@app.put("/api/jobs/{job_id}", dependencies=[Depends(authorized)])
def update_job(job_id: str, body: JobUpdate):
    with store.connect() as db:
        get_job(db, job_id)
        changed = db.execute(
            "UPDATE jobs SET data=?,version=version+1 WHERE id=? AND version=?",
            (json.dumps(body.model_dump(exclude={"version"})), job_id, body.version),
        ).rowcount
        if not changed:
            raise HTTPException(
                409, "Lowongan berubah di sesi lain. Muat ulang sebelum menyimpan."
            )
        store.audit(db, "Kriteria lowongan diperbarui", job_id, now())
        return get_job(db, job_id)


@app.get("/api/jobs/{job_id}/candidates", dependencies=[Depends(authorized)])
def candidates(
    job_id: str, q: str = "", status: str = "all", page: int = 1, size: int = 10
):
    if page < 1 or size not in {10, 20, 50} or len(q) > 120:
        raise HTTPException(422, "Parameter daftar tidak valid.")
    with store.connect() as db:
        job = get_job(db, job_id)
        all_items = [
            store.unpack(r)
            for r in db.execute(
                "SELECT * FROM candidates WHERE job_id=? ORDER BY created_at", (job_id,)
            )
        ]
        latest = db.execute(
            "SELECT * FROM runs WHERE job_id=? ORDER BY created_at DESC LIMIT 1",
            (job_id,),
        ).fetchone()
    run = json.loads(latest["snapshot"]) if latest else None
    results = {r["id"]: r for r in run["results"]} if run else {}
    stale = bool(
        run
        and (
            run["job_version"] != job["version"]
            or run["candidate_ids"] != sorted(c["id"] for c in all_items)
        )
    )
    for item in all_items:
        item["result"] = results.get(item["id"])
    all_items.sort(
        key=lambda c: (c["result"]["rank"] if c["result"] else 999999, c["created_at"])
    )
    counts = {
        s: sum(c["status"] == s for c in all_items)
        for s in ["new", "shortlisted", "hold", "rejected"]
    }
    filtered = [
        c
        for c in all_items
        if (status == "all" or c["status"] == status)
        and q.casefold()
        in (c["profile"]["name"] + " " + " ".join(c["profile"]["skills"])).casefold()
    ]
    total = len(filtered)
    page = min(page, max(1, (total + size - 1) // size))
    return {
        "items": filtered[(page - 1) * size : page * size],
        "total": total,
        "page": page,
        "count": len(all_items),
        "counts": counts,
        "stale": stale,
        "run": {
            "id": latest["id"],
            "created_at": latest["created_at"],
            "engine": run["engine"],
            "weights": run["job"]["weights"],
        }
        if latest
        else None,
    }


def insert_candidate(db, job_id, profile, source, fingerprint=None):
    count = db.execute(
        "SELECT COUNT(*) FROM candidates WHERE job_id=?", (job_id,)
    ).fetchone()[0]
    if count >= 500:
        raise HTTPException(422, "Batas 500 kandidat per lowongan tercapai.")
    cid = uid()
    data = {"profile": profile, "source": source, "status": "new", "note": ""}
    db.execute(
        "INSERT INTO candidates(id,job_id,data,fingerprint,created_at) VALUES(?,?,?,?,?)",
        (cid, job_id, json.dumps(data), fingerprint, now()),
    )
    store.audit(db, "Kandidat ditambahkan", cid, now())
    return cid


@app.post(
    "/api/jobs/{job_id}/candidates", status_code=201, dependencies=[Depends(authorized)]
)
def create_candidate(job_id: str, body: ProfileInput):
    with store.connect() as db:
        get_job(db, job_id)
        return {"id": insert_candidate(db, job_id, body.model_dump(), "manual")}


@app.post(
    "/api/jobs/{job_id}/upload", status_code=201, dependencies=[Depends(authorized)]
)
def upload(job_id: str, file: UploadFile = File(...), use_ai: bool = Form(False)):
    with store.connect() as db:
        job = get_job(db, job_id)
    content = file.file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "PDF maksimal 10 MB.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(422, "Berkas bukan PDF yang valid.")
    digest = hashlib.sha256(content).hexdigest()
    with store.connect() as db:
        if db.execute(
            "SELECT id FROM candidates WHERE job_id=? AND fingerprint=?",
            (job_id, digest),
        ).fetchone():
            raise HTTPException(409, "CV ini sudah diunggah pada lowongan ini.")
    from server.extraction import extract

    try:
        profile, source = extract(content, file.filename or "resume.pdf", job, use_ai)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        log.warning("PDF extraction failed; no candidate saved")
        raise HTTPException(
            422, "PDF gagal diproses. Periksa berkas atau tambahkan profil manual."
        )
    try:
        with store.connect() as db:
            return {
                "id": insert_candidate(db, job_id, profile, source, digest),
                "source": source,
            }
    except sqlite3.IntegrityError:
        raise HTTPException(409, "CV ini sudah diunggah pada lowongan ini.")


@app.patch("/api/candidates/{candidate_id}", dependencies=[Depends(authorized)])
def review(candidate_id: str, body: ReviewInput):
    with store.connect() as db:
        row = db.execute(
            "SELECT * FROM candidates WHERE id=?", (candidate_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Kandidat tidak ditemukan.")
        item = json.loads(row["data"])
        if body.status == "rejected" and not body.note.strip():
            raise HTTPException(422, "Tuliskan alasan keputusan untuk jejak tinjauan.")
        item.update(status=body.status, note=body.note)
        if not db.execute(
            "UPDATE candidates SET data=?,version=version+1 WHERE id=? AND version=?",
            (json.dumps(item), candidate_id, body.version),
        ).rowcount:
            raise HTTPException(
                409, "Profil berubah di sesi lain. Muat ulang sebelum menyimpan."
            )
        store.audit(db, "Tinjauan kandidat: " + body.status, candidate_id, now())
    return {"ok": True}


@app.put("/api/candidates/{candidate_id}/profile", dependencies=[Depends(authorized)])
def edit_profile(candidate_id: str, body: ProfileInput, version: int):
    with store.connect() as db:
        row = db.execute(
            "SELECT * FROM candidates WHERE id=?", (candidate_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Kandidat tidak ditemukan.")
        data = json.loads(row["data"])
        data["profile"] = body.model_dump()
        if not db.execute(
            "UPDATE candidates SET data=?,version=version+1 WHERE id=? AND version=?",
            (json.dumps(data), candidate_id, version),
        ).rowcount:
            raise HTTPException(
                409, "Profil berubah di sesi lain. Muat ulang sebelum menyimpan."
            )
        # Any profile correction invalidates the latest snapshot as well.
        db.execute("UPDATE jobs SET version=version+1 WHERE id=?", (row["job_id"],))
        store.audit(db, "Profil kandidat diverifikasi", candidate_id, now())
    return {"ok": True}


@app.post("/api/jobs/{job_id}/analyze", dependencies=[Depends(authorized)])
def run_analysis(job_id: str):
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        job = get_job(db, job_id)
        items = [
            store.unpack(r)
            for r in db.execute("SELECT * FROM candidates WHERE job_id=?", (job_id,))
        ]
        if len(items) < 2:
            raise HTTPException(
                422, "Tambahkan setidaknya 2 kandidat untuk analisis perbandingan."
            )
        results = analyze(items, job)
        snapshot = {
            "engine": "evidence-mcdm/1.0",
            "job_version": job["version"],
            "job": job,
            "candidate_ids": sorted(c["id"] for c in items),
            "candidates": items,
            "results": results,
        }
        run_id = uid()
        db.execute(
            "INSERT INTO runs VALUES(?,?,?,?)",
            (run_id, job_id, json.dumps(snapshot), now()),
        )
        store.audit(db, "Analisis selesai", run_id, now())
    return {"id": run_id, "count": len(results)}


@app.get("/api/jobs/{job_id}/export", dependencies=[Depends(authorized)])
def export(job_id: str):
    with store.connect() as db:
        get_job(db, job_id)
        row = db.execute(
            "SELECT * FROM runs WHERE job_id=? ORDER BY created_at DESC LIMIT 1",
            (job_id,),
        ).fetchone()
    if not row:
        raise HTTPException(422, "Jalankan analisis sebelum mengekspor.")
    snapshot = json.loads(row["snapshot"])
    profiles = {c["id"]: c for c in snapshot["candidates"]}
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(
        [
            "Peringkat",
            "Nama",
            "Kesesuaian persyaratan (%)",
            "Status saat analisis",
            "ID analisis",
            "Waktu UTC",
            "Versi mesin",
        ]
    )
    for r in snapshot["results"]:
        c = profiles[r["id"]]
        name = c["profile"]["name"]
        if name.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
            name = "'" + name
        writer.writerow(
            [
                r["rank"],
                name,
                r["score"],
                c["status"],
                row["id"],
                row["created_at"],
                snapshot["engine"],
            ]
        )
    return Response(
        "\ufeff" + out.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="recruitai-analysis.csv"'
        },
    )


@app.get("/api/audit", dependencies=[Depends(authorized)])
def audit_log():
    with store.connect() as db:
        return [
            dict(r)
            for r in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 100")
        ]


@app.post("/api/demo", status_code=201, dependencies=[Depends(authorized)])
def demo():
    with store.connect() as db:
        if db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]:
            raise HTTPException(
                409, "Contoh hanya dapat dimuat pada ruang kerja kosong."
            )
        job = JobInput(
            title="Senior Frontend Engineer",
            department="Product & Engineering",
            location="Jakarta · Hybrid",
            required_skills=["React", "TypeScript", "JavaScript", "CSS", "Testing"],
            required_languages=["Indonesia", "Inggris"],
            required_experience_months=48,
        )
        jid = uid()
        db.execute(
            "INSERT INTO jobs(id,data,created_at) VALUES(?,?,?)",
            (jid, job.model_dump_json(), now()),
        )
        examples = [
            (
                "Nadia Putri",
                "Frontend Engineer · 5 tahun",
                60,
                ["React", "TypeScript", "JavaScript", "CSS", "Testing"],
                ["Indonesia", "Inggris"],
            ),
            (
                "Raka Pratama",
                "Software Engineer · 4 tahun",
                48,
                ["React", "TypeScript", "JavaScript", "CSS"],
                ["Indonesia", "Inggris"],
            ),
            (
                "Clara Wijaya",
                "UI Engineer · 3 tahun",
                36,
                ["React", "JavaScript", "CSS", "Testing"],
                ["Indonesia", "Inggris"],
            ),
            (
                "Dimas Saputra",
                "Frontend Developer · 3 tahun",
                36,
                ["React", "TypeScript", "CSS"],
                ["Indonesia"],
            ),
            (
                "Alya Rahman",
                "Web Developer · 2 tahun",
                24,
                ["JavaScript", "CSS", "Testing"],
                ["Indonesia", "Inggris"],
            ),
            (
                "Bima Aditya",
                "Junior Developer · 1 tahun",
                12,
                ["React", "JavaScript", "CSS"],
                ["Indonesia"],
            ),
        ]
        for name, headline, months, skills, langs in examples:
            profile = ProfileInput(
                name=name,
                headline=headline,
                experience_months=months,
                skills=skills,
                languages=langs,
                education="S1",
                summary="Profil fiktif untuk menjelajahi alur seleksi. Bukan kandidat nyata.",
            )
            insert_candidate(db, jid, profile.model_dump(), "demo")
        store.audit(db, "Data contoh fiktif dimuat", jid, now())
    run_analysis(jid)
    return {"id": jid}


app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")


@app.get("/")
def index():
    return FileResponse(ROOT / "web/index.html")
