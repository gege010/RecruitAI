"""
Page 2 — Upload CV Kandidat
Upload PDF dengan AI parsing otomatis dan preview profil.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st

from db.repositories import list_vacancies, create_candidate, list_candidates, delete_candidate
from core.resume_parser import parse_resume

st.set_page_config(page_title="Upload CV · RecruitAI", page_icon="📄", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0f172a, #1e1b4b, #0f3460);
    border-radius: 14px; padding: 1.5rem 2rem; margin-bottom: 1.8rem;
    border-left: 5px solid #a78bfa;
}
.page-header h2 { color: #e2e8f0; margin: 0; font-size: 1.5rem; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; font-size: 0.9rem; }
.cand-preview {
    background: #1e293b; border: 1px solid rgba(100,116,139,0.25);
    border-radius: 12px; padding: 1.2rem 1.4rem; margin-bottom: 0.7rem;
}
.cand-preview-name { color: #c4b5fd; font-weight: 700; font-size: 1rem; margin: 0 0 0.3rem; }
.skill-pill {
    background: #1e3a5f; color: #93c5fd;
    padding: 2px 9px; border-radius: 99px; font-size: 0.73rem;
    display: inline-block; margin: 2px;
}
.cert-pill {
    background: #1e3a1e; color: #6ee7b7;
    padding: 2px 9px; border-radius: 99px; font-size: 0.73rem;
    display: inline-block; margin: 2px;
}
.status-ok  { color: #34d399; font-weight: 700; }
.status-err { color: #f87171; font-weight: 700; }
.status-ocr { color: #f59e0b; font-weight: 700; }
.info-row { display: flex; gap: 1.5rem; margin-top: 0.4rem; flex-wrap: wrap; }
.info-item { font-size: 0.83rem; }
.info-item .label { color: #64748b; }
.info-item .value { color: #e2e8f0; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>📄 Upload CV Kandidat</h2>
  <p>Upload file PDF — AI akan membaca dan mengekstrak informasi kandidat secara otomatis</p>
</div>""", unsafe_allow_html=True)


# ── Vacancy Selector ──────────────────────────────────────────────────────────
try:
    vacancies = list_vacancies()
except Exception:
    vacancies = []

if not vacancies:
    st.warning("⚠️ Belum ada lowongan. Buat lowongan terlebih dahulu di menu **'💼 Kelola Lowongan'**.")
    st.stop()

vacancy_map = {f"{v['title']} ({v['job_family']})": v["id"] for v in vacancies}
selected_label = st.selectbox("Upload CV untuk Lowongan:", list(vacancy_map.keys()))
vacancy_id = vacancy_map[selected_label]


# ── File Upload ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### Upload File CV (PDF)")
st.caption("Mendukung CV berbentuk teks maupun CV yang berupa gambar/scan. Upload beberapa file sekaligus.")

uploaded_files = st.file_uploader(
    "Seret file ke sini atau klik untuk memilih",
    type=["pdf"],
    accept_multiple_files=True,
    key="pdf_uploader",
    label_visibility="collapsed",
)

if uploaded_files:
    st.info(f"**{len(uploaded_files)} file dipilih.** Klik tombol di bawah untuk memproses.")
    parse_btn = st.button("🤖 Proses Semua CV dengan AI", type="primary")

    if parse_btn:
        progress_bar = st.progress(0)
        status_text  = st.empty()
        results_log  = []

        for idx, f in enumerate(uploaded_files):
            status_text.markdown(f"**Memproses: {f.name}** ({idx+1}/{len(uploaded_files)})...")
            progress_bar.progress((idx) / len(uploaded_files))
            pdf_bytes = f.read()

            try:
                raw_text, profile, method = parse_resume(pdf_bytes, f.name)
                create_candidate({
                    "vacancy_id": vacancy_id,
                    "original_filename": f.name,
                    "raw_text": raw_text,
                    "parsed_profile": profile.model_dump(),
                    "parsing_status": "success",
                })
                results_log.append({
                    "filename": f.name, "status": "success",
                    "name": profile.name, "method": method,
                    "skills": len(profile.skills), "exp": len(profile.experience),
                })
            except Exception as e:
                try:
                    create_candidate({
                        "vacancy_id": vacancy_id,
                        "original_filename": f.name,
                        "raw_text": "",
                        "parsing_status": "failed",
                        "parsing_error": str(e),
                    })
                except Exception:
                    pass
                results_log.append({"filename": f.name, "status": "failed", "error": str(e)})

        progress_bar.progress(1.0)
        status_text.empty()

        # Results summary
        n_ok = sum(1 for r in results_log if r["status"] == "success")
        n_ocr = sum(1 for r in results_log if r.get("method") == "ocr")

        st.markdown("#### Hasil Pemrosesan:")
        for r in results_log:
            if r["status"] == "success":
                method_badge = " *(via OCR — scan PDF)*" if r.get("method") == "ocr" else ""
                st.markdown(
                    f'<span class="status-ok">✅ {r["filename"]}</span> — '
                    f'Nama: <strong>{r["name"] or "Tidak terdeteksi"}</strong>, '
                    f'Skill: {r["skills"]}, Pengalaman: {r["exp"]} posisi{method_badge}',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<span class="status-err">❌ {r["filename"]}</span> — Gagal: {r.get("error", "")}',
                    unsafe_allow_html=True
                )

        if n_ok == len(results_log):
            st.success(f"✅ Semua {n_ok} CV berhasil diproses!")
        else:
            st.warning(f"⚠️ {n_ok} dari {len(results_log)} CV berhasil diproses.")

        if n_ocr > 0:
            st.info(f"ℹ️ {n_ocr} file menggunakan OCR (PDF berbentuk gambar/scan). Akurasi mungkin sedikit lebih rendah.")


# ── Candidate List ────────────────────────────────────────────────────────────
st.markdown("---")
col_hdr, col_ref = st.columns([4, 1])
with col_hdr:
    st.markdown("#### Daftar Kandidat yang Sudah Diproses")
with col_ref:
    if st.button("🔄 Refresh"):
        st.rerun()

try:
    candidates = list_candidates(vacancy_id)
except Exception:
    candidates = []

if not candidates:
    st.info("Belum ada CV yang diupload untuk lowongan ini.")
else:
    n_ok = sum(1 for c in candidates if c.get("parsing_status") == "success")
    st.caption(f"{len(candidates)} CV total · {n_ok} berhasil diproses · {len(candidates)-n_ok} gagal/pending")

    for c in candidates:
        profile_data = c.get("parsed_profile") or {}
        name      = profile_data.get("name") or c["original_filename"]
        skills    = profile_data.get("skills", [])[:10]
        certs     = profile_data.get("certifications", [])[:5]
        exp_list  = profile_data.get("experience", [])
        edu_list  = profile_data.get("education", [])
        total_exp = sum(e.get("duration_months", 0) for e in exp_list)
        status    = c.get("parsing_status", "pending")
        langs     = profile_data.get("languages", [])

        icon = "✅" if status == "success" else "❌"

        with st.expander(f"{icon} **{name}** · {c['original_filename']}"):
            col_info, col_del = st.columns([6, 1])

            with col_info:
                # Top info row
                edu_text = "—"
                if edu_list:
                    e0 = edu_list[0]
                    edu_text = f"{e0.get('degree','')} {e0.get('field','')} – {e0.get('institution','')}"

                latest_exp = "—"
                if exp_list:
                    ex0 = exp_list[0]
                    latest_exp = f"{ex0.get('title','')} di {ex0.get('company','')}"

                st.markdown(f"""
                <div class="info-row">
                    <div class="info-item"><div class="label">Email</div><div class="value">{profile_data.get('email','—')}</div></div>
                    <div class="info-item"><div class="label">Lokasi</div><div class="value">{profile_data.get('location','—')}</div></div>
                    <div class="info-item"><div class="label">Pendidikan</div><div class="value">{edu_text}</div></div>
                    <div class="info-item"><div class="label">Total Pengalaman</div><div class="value">{total_exp} bulan ({len(exp_list)} posisi)</div></div>
                    <div class="info-item"><div class="label">Posisi Terakhir</div><div class="value">{latest_exp}</div></div>
                </div>""", unsafe_allow_html=True)

                if langs:
                    st.markdown(f"<div style='margin-top:6px;font-size:0.82rem;color:#64748b'>Bahasa: {', '.join(langs)}</div>", unsafe_allow_html=True)

                if skills:
                    pills = " ".join(f'<span class="skill-pill">{s}</span>' for s in skills)
                    st.markdown(f"<div style='margin-top:8px'><span style='color:#64748b;font-size:0.8rem'>Skill: </span>{pills}</div>", unsafe_allow_html=True)

                if certs:
                    cert_pills = " ".join(f'<span class="cert-pill">{s}</span>' for s in certs)
                    st.markdown(f"<div style='margin-top:6px'><span style='color:#64748b;font-size:0.8rem'>Sertifikasi: </span>{cert_pills}</div>", unsafe_allow_html=True)

                if status == "failed":
                    st.error(f"Error: {c.get('parsing_error','Tidak diketahui')}")

            with col_del:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Hapus", key=f"del_cand_{c['id']}", use_container_width=True):
                    try:
                        delete_candidate(c["id"])
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
