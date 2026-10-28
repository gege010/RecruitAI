"""
Page 4 — Jalankan Analisis
Satu klik untuk menjalankan seluruh pipeline analisis kandidat.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import pandas as pd
import time

from db.repositories import (
    list_vacancies, list_candidates, get_ahp_matrix,
    upsert_scoring_result, delete_scoring_results, get_scoring_results,
)
from core.resume_parser import CandidateProfile
from core.dimension_calculator import compute_dimensions
from core.mcdm.saw import run_saw
from core.mcdm.weighted_product import run_wp
from core.mcdm.topsis import run_topsis
from core.mcdm.ensemble import run_ensemble
from core.llm_explainer import generate_explanation

st.set_page_config(page_title="Analisis Kandidat · RecruitAI", page_icon="🚀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0a0a1a, #1a1a3e, #0d2137);
    border-radius: 14px; padding: 1.5rem 2rem; margin-bottom: 1.8rem;
    border-left: 5px solid #f59e0b;
}
.page-header h2 { color: #fef9c3; margin: 0; font-size: 1.5rem; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; font-size: 0.9rem; }
.checklist-item {
    display: flex; align-items: center; gap: 12px;
    padding: 0.9rem 1.2rem;
    background: #1e293b; border-radius: 10px; margin-bottom: 0.5rem;
    border: 1px solid rgba(100,116,139,0.25);
}
.check-icon { font-size: 1.4rem; flex-shrink: 0; }
.check-text { flex: 1; }
.check-title { color: #e2e8f0; font-weight: 600; font-size: 0.9rem; }
.check-sub   { color: #64748b; font-size: 0.8rem; margin-top: 1px; }
.check-ok    { color: #34d399; font-weight: 700; }
.check-err   { color: #f87171; font-weight: 700; }
.log-container {
    background: #0d1117; border: 1px solid #21262d;
    border-radius: 10px; padding: 1rem 1.2rem; max-height: 280px;
    overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.82rem;
}
.log-ok   { color: #3fb950; }
.log-err  { color: #f85149; }
.log-info { color: #58a6ff; }
.log-warn { color: #e3b341; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>🚀 Jalankan Analisis Kandidat</h2>
  <p>Sistem akan membandingkan semua kandidat dan menghasilkan peringkat secara otomatis</p>
</div>""", unsafe_allow_html=True)


# ── Vacancy Selector ──────────────────────────────────────────────────────────
try:
    vacancies = list_vacancies()
except Exception:
    vacancies = []

if not vacancies:
    st.warning("Belum ada lowongan. Buat lowongan terlebih dahulu.")
    st.stop()

vacancy_map = {f"{v['title']} ({v['job_family']})": v for v in vacancies}
selected_label = st.selectbox("Pilih Lowongan yang Akan Dianalisis", list(vacancy_map.keys()))
vacancy = vacancy_map[selected_label]
vacancy_id = vacancy["id"]

st.markdown("<br>", unsafe_allow_html=True)

# ── Pre-flight Checklist ──────────────────────────────────────────────────────
st.markdown("### ✅ Persiapan Analisis")

try:
    candidates = list_candidates(vacancy_id)
    n_ok = sum(1 for c in candidates if c.get("parsing_status") == "success")
except Exception:
    candidates, n_ok = [], 0

try:
    ahp = get_ahp_matrix(vacancy_id)
    ahp_ok = ahp and ahp.get("is_valid")
    weights = ahp["weights"] if ahp_ok else None
except Exception:
    ahp_ok, weights = False, None

try:
    existing_results = get_scoring_results(vacancy_id)
    has_existing = len(existing_results) > 0
except Exception:
    has_existing = False

# Checklist items
def checklist_item(icon, title, sub, status_text, is_ok):
    cls = "check-ok" if is_ok else "check-err"
    return f"""
    <div class="checklist-item">
        <div class="check-icon">{icon}</div>
        <div class="check-text">
            <div class="check-title">{title}</div>
            <div class="check-sub">{sub}</div>
        </div>
        <div class="{cls}">{status_text}</div>
    </div>"""

st.markdown(
    checklist_item("📄", "CV Kandidat Siap",
                   f"{len(candidates)} CV ditemukan, {n_ok} berhasil dibaca AI",
                   "✓ Siap" if n_ok >= 2 else f"✗ Perlu min. 2 CV (sekarang: {n_ok})",
                   n_ok >= 2),
    unsafe_allow_html=True
)
st.markdown(
    checklist_item("⚖️", "Prioritas Kriteria Sudah Diatur",
                   "Bobot kriteria diperlukan untuk perbandingan",
                   "✓ Sudah diatur" if ahp_ok else "✗ Belum diatur — buka menu 'Atur Prioritas'",
                   ahp_ok),
    unsafe_allow_html=True
)
if has_existing:
    st.markdown(
        checklist_item("🔄", "Hasil Sebelumnya Ditemukan",
                       "Hasil lama akan diganti saat analisis dijalankan ulang",
                       "ℹ️ Ada hasil sebelumnya", True),
        unsafe_allow_html=True
    )

all_ready = n_ok >= 2 and ahp_ok

st.markdown("<br>", unsafe_allow_html=True)

# ── Options & Run ─────────────────────────────────────────────────────────────
st.markdown("### ⚙️ Opsi Analisis")
col_opt, col_btn = st.columns([3, 2])

with col_opt:
    include_ai = st.checkbox(
        "🤖 Buat penjelasan AI untuk setiap kandidat",
        value=True,
        help="AI akan menulis ulasan singkat per kandidat dalam Bahasa Indonesia. Proses lebih lama namun hasil lebih informatif."
    )
    if has_existing:
        overwrite = st.checkbox("♻️ Timpa hasil analisis sebelumnya", value=True)
    else:
        overwrite = True

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button(
        "🚀  Mulai Analisis Sekarang",
        type="primary",
        disabled=not all_ready,
        use_container_width=True,
    )

if not all_ready:
    if n_ok < 2:
        st.error(f"⚠️ Butuh minimal 2 CV yang berhasil dibaca. Sekarang hanya ada **{n_ok}**. Upload lebih banyak CV.")
    if not ahp_ok:
        st.error("⚠️ Prioritas kriteria belum diatur. Buka menu **'⚖️ Atur Prioritas'** terlebih dahulu.")


# ── Run Pipeline ──────────────────────────────────────────────────────────────
if run_btn and all_ready:
    logs = []

    def log(msg, level="info"):
        ts = time.strftime("%H:%M:%S")
        logs.append((f"[{ts}] {msg}", level))

    log_box = st.empty()

    def refresh_log():
        html = '<div class="log-container">'
        for msg, lvl in logs:
            html += f'<div class="log-{lvl}">{msg}</div>'
        html += '</div>'
        log_box.markdown(html, unsafe_allow_html=True)

    st.markdown("### 📋 Progress Analisis")
    progress_bar = st.progress(0)
    status_text  = st.empty()

    log("▶ Memulai analisis...", "info")
    refresh_log()

    # Step 1: Load candidates
    status_text.markdown("**Memuat data kandidat...**")
    parsed_candidates = []
    for c in candidates:
        if c.get("parsing_status") != "success" or not c.get("parsed_profile"):
            continue
        profile = CandidateProfile(**c["parsed_profile"])
        parsed_candidates.append({"db": c, "profile": profile})

    log(f"✓ {len(parsed_candidates)} profil kandidat dimuat", "ok")
    progress_bar.progress(15)
    refresh_log()

    # Step 2: Dimension scores
    status_text.markdown("**Menghitung skor kesesuaian kandidat...**")
    dim_rows = {}
    for item in parsed_candidates:
        cid = item["db"]["id"]
        dims = compute_dimensions(item["profile"], vacancy)
        dim_rows[cid] = dims
        name = item["profile"].name or item["db"]["original_filename"]
        log(f"  ✓ {name} — pendidikan:{dims['education']:.2f} pengalaman:{dims['experience']:.2f} skill:{dims['skills']:.2f}", "ok")

    progress_bar.progress(35)
    refresh_log()

    # Step 3: Decision matrix
    criteria_order = ["education", "experience", "skills", "certifications", "languages"]
    dm_data = {cid: [dims[c] for c in criteria_order] for cid, dims in dim_rows.items()}
    dm = pd.DataFrame.from_dict(dm_data, orient="index", columns=criteria_order)
    log(f"✓ Matriks perbandingan siap ({dm.shape[0]} kandidat × {dm.shape[1]} kriteria)", "info")
    progress_bar.progress(45)
    refresh_log()

    # Step 4: MCDM
    status_text.markdown("**Menjalankan algoritma perbandingan...**")
    saw_scores    = run_saw(dm, weights)
    wp_scores     = run_wp(dm, weights)
    topsis_scores = run_topsis(dm, weights)
    ensemble_df   = run_ensemble({"SAW": saw_scores, "WP": wp_scores, "TOPSIS": topsis_scores})
    log("✓ Analisis multi-kriteria selesai (3 metode)", "ok")
    progress_bar.progress(60)
    refresh_log()

    # Step 5: Save & AI explanations
    if overwrite:
        try:
            delete_scoring_results(vacancy_id)
        except Exception:
            pass

    n_total = len(ensemble_df)
    for idx, (_, row) in enumerate(ensemble_df.iterrows()):
        cid  = row["candidate_id"]
        item = next(x for x in parsed_candidates if x["db"]["id"] == cid)
        profile = item["profile"]
        dims = dim_rows[cid]
        rank = int(row["ensemble_rank"])
        name = profile.name or item["db"]["original_filename"]

        ai_text = ""
        if include_ai:
            status_text.markdown(f"**Membuat ulasan AI untuk kandidat #{rank}: {name}...**")
            log(f"  🤖 Menyusun ulasan AI untuk #{rank} {name}...", "info")
            refresh_log()
            ai_text = generate_explanation(
                candidate_name=name,
                ensemble_rank=rank,
                dimension_scores=dims,
                saw_score=float(row["SAW_score"]),
                wp_score=float(row["WP_score"]),
                topsis_score=float(row["TOPSIS_score"]),
                vacancy_title=vacancy["title"],
                vacancy_requirements=vacancy,
                candidate_profile=profile.model_dump(),
            )

        upsert_scoring_result({
            "vacancy_id": vacancy_id,
            "candidate_id": cid,
            "dimension_scores": dims,
            "normalized_scores": dm.loc[cid].to_dict(),
            "saw_score":     float(row["SAW_score"]),
            "saw_rank":      int(row["SAW_rank"]),
            "wp_score":      float(row["WP_score"]),
            "wp_rank":       int(row["WP_rank"]),
            "topsis_score":  float(row["TOPSIS_score"]),
            "topsis_rank":   int(row["TOPSIS_rank"]),
            "borda_score":   int(row["borda_score"]),
            "ensemble_rank": rank,
            "ai_explanation": ai_text,
        })

        progress_bar.progress(60 + int(40 * (idx + 1) / n_total))
        log(f"  ✓ #{rank} {name} berhasil disimpan", "ok")
        refresh_log()

    progress_bar.progress(100)
    status_text.empty()
    log("🎉 Analisis selesai! Buka menu 'Lihat Hasil' untuk melihat peringkat.", "ok")
    refresh_log()

    st.success("✅ Analisis selesai! Silakan buka **📊 Lihat Hasil** di menu sebelah kiri.")
