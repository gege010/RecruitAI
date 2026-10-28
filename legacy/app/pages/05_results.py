"""
Page 5 — Lihat Hasil Seleksi
Dashboard HR-friendly: peringkat kandidat + rekomendasi AI.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io

from db.repositories import list_vacancies, get_scoring_results
from core.llm_explainer import generate_summary_report, generate_quick_fit

st.set_page_config(page_title="Hasil Seleksi · RecruitAI", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0f0c29, #1e1b4b, #16213e);
    border-radius: 14px; padding: 1.5rem 2rem; margin-bottom: 1.8rem;
    border-left: 5px solid #34d399;
}
.page-header h2 { color: #ecfdf5; margin: 0; font-size: 1.5rem; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; font-size: 0.9rem; }

/* ─── Candidate card ─────────────────────────────────── */
.cand-card {
    border-radius: 14px; padding: 1.4rem 1.6rem; margin-bottom: 1rem;
    border: 1px solid; transition: box-shadow 0.2s;
}
.cand-card:hover { box-shadow: 0 8px 30px rgba(0,0,0,0.3); }
.cand-rank-1 { background: linear-gradient(135deg,#1a1500,#2a2000); border-color: #fbbf24; }
.cand-rank-2 { background: linear-gradient(135deg,#111827,#1a2535); border-color: #94a3b8; }
.cand-rank-3 { background: linear-gradient(135deg,#1a0f00,#2a1800); border-color: #b45309; }
.cand-rank-n { background: #1e293b; border-color: rgba(100,116,139,0.3); }

.medal { font-size: 2rem; }
.cand-name { color: #f1f5f9; font-size: 1.1rem; font-weight: 700; margin: 0; }
.cand-file { color: #475569; font-size: 0.8rem; }

/* Score bars */
.score-bar-row {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 5px;
}
.sbl { width: 120px; color: #94a3b8; font-size: 0.78rem; }
.sbw { flex: 1; background: #0f172a; border-radius: 99px; height: 10px; }
.sbf { height: 10px; border-radius: 99px; }
.sbv { width: 40px; color: #e2e8f0; font-size: 0.78rem; text-align: right; font-weight: 600; }

/* Fit badge */
.fit-badge {
    display: inline-block; padding: 4px 12px; border-radius: 99px;
    font-size: 0.8rem; font-weight: 600; margin-top: 6px;
}
.fit-high   { background: #064e3b; color: #34d399; }
.fit-medium { background: #1c2900; color: #a3e635; }
.fit-low    { background: #2d1f00; color: #fb923c; }
.fit-poor   { background: #3b0000; color: #f87171; }

/* Explanation box */
.explain-box {
    background: #0f172a; border: 1px solid #1e3a5f;
    border-radius: 10px; padding: 1rem 1.2rem; margin-top: 0.8rem;
    color: #cbd5e1; font-size: 0.87rem; line-height: 1.7;
    border-left: 3px solid #3b82f6;
}

/* Summary box */
.summary-box {
    background: linear-gradient(135deg,#0f172a,#1e1b4b);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 12px; padding: 1.4rem 1.6rem;
    color: #e2e8f0; font-size: 0.9rem; line-height: 1.8;
}

/* Comparison table */
.comp-label { color: #64748b; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>📊 Hasil Seleksi Kandidat</h2>
  <p>Peringkat otomatis berdasarkan kesesuaian profil dengan persyaratan posisi</p>
</div>""", unsafe_allow_html=True)


# ── Vacancy Selector ──────────────────────────────────────────────────────────
try:
    vacancies = list_vacancies()
except Exception:
    vacancies = []

if not vacancies:
    st.warning("Belum ada lowongan ditemukan.")
    st.stop()

vacancy_map = {f"{v['title']} ({v['job_family']})": v for v in vacancies}
selected_label = st.selectbox("Pilih Lowongan", list(vacancy_map.keys()))
vacancy = vacancy_map[selected_label]
vacancy_id = vacancy["id"]


# ── Load Results ──────────────────────────────────────────────────────────────
try:
    results = get_scoring_results(vacancy_id)
except Exception as e:
    st.error(f"Tidak dapat memuat hasil: {e}")
    results = []

if not results:
    st.info("💡 Belum ada hasil analisis untuk lowongan ini. Jalankan analisis dari menu **'🚀 Jalankan Analisis'** terlebih dahulu.")
    st.stop()


# ── Build DataFrame ───────────────────────────────────────────────────────────
CRIT_LABELS = {
    "education": "Pendidikan",
    "experience": "Pengalaman",
    "skills": "Keahlian",
    "certifications": "Sertifikasi",
    "languages": "Bahasa",
}
BAR_COLORS = {
    "education": "#818cf8",
    "experience": "#34d399",
    "skills": "#f59e0b",
    "certifications": "#60a5fa",
    "languages": "#a78bfa",
}

rows = []
for r in results:
    cand = r.get("candidates") or {}
    profile = cand.get("parsed_profile") or {}
    dims = r.get("dimension_scores") or {}
    overall = sum(dims.values()) / len(dims) if dims else 0
    rows.append({
        "rank":        r["ensemble_rank"],
        "name":        profile.get("name") or cand.get("original_filename", "Unknown"),
        "filename":    cand.get("original_filename", ""),
        "overall":     round(overall, 3),
        "education":   dims.get("education", 0),
        "experience":  dims.get("experience", 0),
        "skills":      dims.get("skills", 0),
        "certifications": dims.get("certifications", 0),
        "languages":   dims.get("languages", 0),
        "explanation": r.get("ai_explanation", ""),
        "candidate_id": r["candidate_id"],
        "dimension_scores": dims,
    })

df = pd.DataFrame(rows).sort_values("rank").reset_index(drop=True)
dim_cols = ["education", "experience", "skills", "certifications", "languages"]


# ── Section 1: Summary Card (AI) ──────────────────────────────────────────────
st.markdown("## 📝 Ringkasan Hasil Seleksi")

col_sum, col_meta = st.columns([3, 1])

with col_meta:
    st.metric("Total Kandidat", len(df))
    best = df.iloc[0]
    st.metric("Kandidat Terbaik", best["name"][:20] + ("..." if len(best["name"]) > 20 else ""))
    avg_overall = df["overall"].mean()
    st.metric("Rata-rata Kesesuaian", f"{avg_overall:.0%}")

with col_sum:
    if st.button("🤖 Buat Ringkasan Otomatis (AI)", use_container_width=False):
        with st.spinner("AI sedang menyusun ringkasan..."):
            # Pass rich data: actual names + detailed scores
            top_data_rich = []
            for _, r in df.head(3).iterrows():
                top_data_rich.append({
                    "rank": int(r["rank"]),
                    "name": r["name"],
                    "filename": r["filename"],
                    "overall": r["overall"],
                    "dimension_scores": r["dimension_scores"],
                    "education": r["education"],
                    "experience": r["experience"],
                    "skills": r["skills"],
                    "certifications": r["certifications"],
                    "languages": r["languages"],
                })
            summary = generate_summary_report(
                vacancy["title"],
                top_data_rich,
                vacancy_requirements=vacancy,
            )
            st.session_state["exec_summary"] = summary
            # Reset when vacancy changes
            st.session_state["exec_summary_vacancy"] = vacancy_id

    # Clear summary if vacancy changed
    if st.session_state.get("exec_summary_vacancy") != vacancy_id:
        st.session_state.pop("exec_summary", None)

    if "exec_summary" in st.session_state:
        st.markdown(f'<div class="summary-box">{st.session_state["exec_summary"]}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown("""<div class="summary-box" style="color:#475569;font-style:italic">
        Klik tombol di atas untuk mendapatkan ringkasan dan rekomendasi otomatis dari AI.</div>""",
                    unsafe_allow_html=True)


# ── Section 2: Candidate Cards ────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🏆 Peringkat Kandidat")

medals = {1: "🥇", 2: "🥈", 3: "🥉"}
card_cls = {1: "cand-rank-1", 2: "cand-rank-2", 3: "cand-rank-3"}

top_n = st.slider("Tampilkan peringkat teratas:", 1, len(df), min(len(df), 10))

for _, row in df.head(top_n).iterrows():
    rank = int(row["rank"])
    medal = medals.get(rank, f"#{rank}")
    cls = card_cls.get(rank, "cand-rank-n")
    overall_pct = int(row["overall"] * 100)

    # Build score bars HTML — use percentage width (100% = full bar)
    bars_html = ""
    for dim in dim_cols:
        score = row[dim]
        width_pct = int(score * 100)  # 0–100%
        color = BAR_COLORS[dim]
        label = CRIT_LABELS[dim]
        bars_html += f"""
        <div class="score-bar-row">
            <div class="sbl">{label}</div>
            <div class="sbw"><div class="sbf" style="width:{width_pct}%;background:{color}"></div></div>
            <div class="sbv">{score:.0%}</div>
        </div>"""

    # Fit badge
    fit_text = generate_quick_fit(row["name"], row["dimension_scores"], vacancy["title"])
    if "✅" in fit_text:   fit_cls = "fit-high"
    elif "🟡" in fit_text: fit_cls = "fit-medium"
    elif "🟠" in fit_text: fit_cls = "fit-low"
    else:                   fit_cls = "fit-poor"

    st.markdown(f"""
    <div class="cand-card {cls}">
        <div style="display:flex;align-items:flex-start;gap:1rem">
            <div class="medal">{medal}</div>
            <div style="flex:1">
                <div class="cand-name">{row['name']}</div>
                <div class="cand-file">{row['filename']}</div>
                <div class="fit-badge {fit_cls}">{fit_text}</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:2rem;font-weight:800;color:#a78bfa">{overall_pct}%</div>
                <div style="color:#64748b;font-size:0.75rem">Kesesuaian</div>
            </div>
        </div>
        <div style="margin-top:1rem">{bars_html}</div>
    </div>""", unsafe_allow_html=True)

    if row["explanation"]:
        with st.expander(f"📋 Baca penilaian AI untuk {row['name']}"):
            st.markdown(f'<div class="explain-box">{row["explanation"]}</div>', unsafe_allow_html=True)


# ── Section 3: Comparison Table ───────────────────────────────────────────────
st.markdown("---")
st.markdown("## 📋 Tabel Perbandingan Lengkap")
st.caption("Nilai 100% = memenuhi sepenuhnya. Nilai 0% = tidak memenuhi kriteria.")

display_df = df[["rank", "name", "overall"] + dim_cols].copy()
display_df.columns = ["Peringkat", "Nama Kandidat", "Kesesuaian Akhir",
                      "Pendidikan", "Pengalaman", "Keahlian", "Sertifikasi", "Bahasa"]

score_cols = ["Kesesuaian Akhir", "Pendidikan", "Pengalaman", "Keahlian", "Sertifikasi", "Bahasa"]
st.dataframe(
    display_df.style
    .format({c: "{:.0%}" for c in score_cols})
    .background_gradient(subset=score_cols, cmap="RdYlGn", vmin=0, vmax=1),
    use_container_width=True,
    height=min(500, len(df) * 40 + 60),
)


# ── Section 4: Radar Comparison ───────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🕸️ Perbandingan Profil Kandidat")
st.caption("Pilih kandidat untuk dibandingkan secara visual. Setiap garis mewakili satu kandidat.")

# Use (rank, name, candidate_id) tuples to handle duplicate names
option_labels = [f"#{int(r['rank'])} — {r['name']} ({r['filename']})" for _, r in df.iterrows()]
option_to_idx  = {lbl: i for i, lbl in enumerate(option_labels)}

radar_selected_labels = st.multiselect(
    "Pilih kandidat yang ingin dibandingkan",
    options=option_labels,
    default=option_labels[:min(3, len(option_labels))],
)

if radar_selected_labels:
    colors = ["#a78bfa", "#34d399", "#f59e0b", "#60a5fa", "#f87171", "#c084fc"]
    dim_labels = [CRIT_LABELS[d] for d in dim_cols]
    fig = go.Figure()

    for i, lbl in enumerate(radar_selected_labels):
        idx = option_to_idx[lbl]
        row = df.iloc[idx]  # Use positional index — avoids name collision
        vals = [float(row[d]) for d in dim_cols]
        vals_c = vals + [vals[0]]
        lbls_c = dim_labels + [dim_labels[0]]
        c = colors[i % len(colors)]
        r_hex, g_hex, b_hex = c[1:3], c[3:5], c[5:7]
        fill_rgba = f"rgba({int(r_hex,16)},{int(g_hex,16)},{int(b_hex,16)},0.15)"
        display_name = f"#{int(row['rank'])} {row['name']}"
        fig.add_trace(go.Scatterpolar(
            r=vals_c, theta=lbls_c,
            fill="toself",
            fillcolor=fill_rgba,
            line=dict(color=c, width=2.5),
            name=display_name,
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1],
                            tickformat=".0%", tickfont=dict(size=9, color="#64748b")),
            angularaxis=dict(tickfont=dict(size=11, color="#e2e8f0")),
        ),
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        legend=dict(bgcolor="#1e293b", bordercolor="#334155", borderwidth=1),
        height=480, margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Pilih minimal 1 kandidat untuk menampilkan grafik.")


# ── Section 5: Export ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 💾 Unduh Hasil Seleksi")

col_xl, col_csv = st.columns(2)

export_df = df[["rank", "name", "filename", "overall"] + dim_cols + ["explanation"]].copy()
export_df.columns = ["Peringkat", "Nama", "File CV", "Kesesuaian",
                     "Pendidikan", "Pengalaman", "Keahlian", "Sertifikasi", "Bahasa", "Penilaian AI"]

with col_xl:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Hasil Seleksi")
    st.download_button(
        "📥 Unduh Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"hasil_seleksi_{vacancy['title'].replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with col_csv:
    csv_data = export_df.drop(columns=["Penilaian AI"]).to_csv(index=False)
    st.download_button(
        "📥 Unduh CSV",
        data=csv_data,
        file_name=f"hasil_seleksi_{vacancy['title'].replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
