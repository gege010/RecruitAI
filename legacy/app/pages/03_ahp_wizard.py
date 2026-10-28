"""
Page 3 — Atur Prioritas Kriteria (AHP Wizard)
Antarmuka intuitif untuk menetapkan bobot kriteria.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from app.config import AHP_CRITERIA
from core.mcdm.ahp import compute_ahp, build_reciprocal_matrix
from db.repositories import list_vacancies, save_ahp_matrix, get_ahp_matrix

st.set_page_config(page_title="Prioritas Kriteria · RecruitAI", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #1a0533, #2d1b69);
    border-radius: 14px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    border-left: 5px solid #f59e0b;
}
.page-header h2 { color: #fef3c7; margin: 0; font-size: 1.5rem; }
.page-header p  { color: #94a3b8; margin: 0.3rem 0 0; font-size: 0.9rem; }
.info-box {
    background: #1e293b; border: 1px solid rgba(96,165,250,0.25);
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 1rem;
    font-size: 0.88rem; color: #94a3b8; line-height: 1.6;
}
.pair-row {
    background: #1e293b; border: 1px solid rgba(100,116,139,0.2);
    border-radius: 10px; padding: 0.8rem 1.2rem; margin-bottom: 0.5rem;
    transition: border-color 0.2s;
}
.pair-row:hover { border-color: #a78bfa; }
.crit-left  { color: #a78bfa; font-weight: 700; font-size: 0.95rem; }
.crit-right { color: #60a5fa; font-weight: 700; font-size: 0.95rem; }
.weight-row {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 8px; padding: 6px 0;
}
.weight-label { width: 130px; color: #e2e8f0; font-weight: 600; font-size: 0.88rem; }
.weight-bar-bg {
    flex: 1; background: #0f172a; border-radius: 99px; height: 18px;
    position: relative;
}
.weight-bar-fill {
    height: 18px; border-radius: 99px;
    background: linear-gradient(90deg, #7c3aed, #a78bfa);
}
.weight-pct { color: #a78bfa; font-weight: 700; font-size: 0.85rem; width: 50px; text-align: right; }
.cr-ok   { background: #064e3b; color: #34d399; padding: 8px 16px; border-radius: 10px; font-weight: 700; display: inline-block; }
.cr-warn { background: #7f1d1d; color: #f87171; padding: 8px 16px; border-radius: 10px; font-weight: 700; display: inline-block; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>⚖️ Atur Prioritas Kriteria Seleksi</h2>
  <p>Tentukan seberapa penting masing-masing kriteria untuk posisi yang dibuka</p>
</div>""", unsafe_allow_html=True)


# ── Vacancy Selector ──────────────────────────────────────────────────────────
try:
    vacancies = list_vacancies()
except Exception:
    vacancies = []

if not vacancies:
    st.warning("⚠️ Belum ada lowongan. Buat lowongan terlebih dahulu.")
    st.stop()

vacancy_map = {f"{v['title']} ({v['job_family']})": v for v in vacancies}
selected_label = st.selectbox("Pilih Lowongan yang Akan Dikonfigurasi", list(vacancy_map.keys()))
vacancy = vacancy_map[selected_label]
vacancy_id = vacancy["id"]

# Load existing
existing = None
try:
    existing = get_ahp_matrix(vacancy_id)
except Exception:
    pass

if existing and existing.get("is_valid"):
    st.success(f"✅ Prioritas sudah disimpan sebelumnya untuk lowongan ini (tingkat konsistensi: {existing.get('consistency_ratio', 0):.3f}). Anda bisa mengubahnya di bawah.")


# ── Human-friendly criteria labels ───────────────────────────────────────────
CRIT_LABELS = {
    "Education":      ("🎓 Pendidikan",     "Tingkat dan bidang pendidikan"),
    "Experience":     ("💼 Pengalaman",      "Lama dan relevansi pengalaman kerja"),
    "Skills":         ("🛠️ Keahlian",        "Kesesuaian skill teknis dan non-teknis"),
    "Certifications": ("📜 Sertifikasi",     "Memiliki sertifikasi yang relevan"),
    "Languages":      ("🌐 Bahasa",          "Kemampuan bahasa yang dibutuhkan"),
}

n = len(AHP_CRITERIA)

# Pre-fill defaults from existing data
upper_defaults: dict[tuple[int, int], float] = {}
if existing and existing.get("pairwise_matrix"):
    mat = existing["pairwise_matrix"]
    for i in range(n):
        for j in range(i + 1, n):
            upper_defaults[(i, j)] = mat[i][j]


# ── Layout: Side-by-side (Step 1 & 2 on same row) ───────────────────────────
st.markdown("---")
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown("### Langkah 1: Bandingkan Antar Kriteria")
    st.markdown('<div class="info-box">Untuk setiap pasang kriteria, geser slider ke kiri jika kriteria <strong style="color:#a78bfa">kiri lebih penting</strong>, atau ke kanan jika kriteria <strong style="color:#60a5fa">kanan lebih penting</strong>. Posisi tengah berarti sama pentingnya.</div>', unsafe_allow_html=True)

    upper_vals: dict[tuple[int, int], float] = {}

    for i in range(n):
        for j in range(i + 1, n):
            label_i = CRIT_LABELS[AHP_CRITERIA[i]][0]
            label_j = CRIT_LABELS[AHP_CRITERIA[j]][0]
            default_val = float(upper_defaults.get((i, j), 1.0))

            with st.container():
                st.markdown(f"""<div class="pair-row">
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem">
                        <span class="crit-left">{label_i}</span>
                        <span style="color:#475569;font-size:0.8rem">vs</span>
                        <span class="crit-right">{label_j}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

                val = st.select_slider(
                    f"_{i}_{j}",
                    options=[1/9, 1/7, 1/5, 1/3, 1.0, 3.0, 5.0, 7.0, 9.0],
                    value=min([1/9, 1/7, 1/5, 1/3, 1.0, 3.0, 5.0, 7.0, 9.0],
                              key=lambda x: abs(x - default_val)),
                    format_func=lambda x: (
                        f"← {label_i} jauh lebih penting ({int(round(1/x))}x)" if x < 0.5 else
                        f"← {label_i} lebih penting ({int(round(1/x))}x)" if x < 1.0 else
                        "Sama pentingnya" if x == 1.0 else
                        f"{label_j} lebih penting ({int(x)}x) →" if x <= 5.0 else
                        f"{label_j} jauh lebih penting ({int(x)}x) →"
                    ),
                    label_visibility="collapsed",
                    key=f"ahp_{i}_{j}",
                )
                upper_vals[(i, j)] = val


with col_right:
    st.markdown("### Langkah 2: Hitung & Simpan")
    st.markdown('<div class="info-box">Setelah mengatur semua perbandingan, klik tombol di bawah untuk menghitung bobot dan memeriksa konsistensi pilihan Anda.</div>', unsafe_allow_html=True)

    compute_btn = st.button("⚡ Hitung Bobot Kriteria", type="primary", use_container_width=True)

    if compute_btn:
        matrix = build_reciprocal_matrix(upper_vals, n)
        result = compute_ahp(matrix)
        st.session_state["ahp_result"] = result
        st.session_state["ahp_matrix"] = matrix

    if "ahp_result" in st.session_state:
        result = st.session_state["ahp_result"]
        weights = result["weights"]
        cr = result["consistency_ratio"]

        st.markdown("<br>", unsafe_allow_html=True)

        # CR status — plain language
        if result["is_valid"]:
            st.markdown('<div class="cr-ok">✅ Pilihan Anda konsisten dan dapat digunakan</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="cr-warn">⚠️ Pilihan kurang konsisten — harap revisi perbandingan</div>', unsafe_allow_html=True)
            st.caption("Tips: Pastikan pilihan Anda tidak saling bertentangan. Misalnya, jika A > B dan B > C, maka A harus > C.")

        # Weight bars
        st.markdown("<br>**Bobot Kriteria yang Dihasilkan:**")
        for crit, w in zip(AHP_CRITERIA, weights):
            label, desc = CRIT_LABELS[crit]
            bar_pct = int(w * 100)
            bar_width = int(w * 300)
            st.markdown(f"""
            <div class="weight-row">
                <div class="weight-label">{label}</div>
                <div class="weight-bar-bg">
                    <div class="weight-bar-fill" style="width:{bar_width}px"></div>
                </div>
                <div class="weight-pct">{bar_pct}%</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Save button
        if result["is_valid"]:
            if st.button("💾 Simpan Prioritas Ini", type="primary", use_container_width=True):
                try:
                    save_ahp_matrix({
                        "vacancy_id": vacancy_id,
                        "criteria_names": AHP_CRITERIA,
                        "pairwise_matrix": st.session_state["ahp_matrix"],
                        "weights": weights,
                        "lambda_max": result["lambda_max"],
                        "consistency_index": result["consistency_index"],
                        "consistency_ratio": cr,
                        "is_valid": True,
                    })
                    st.success("✅ Prioritas kriteria berhasil disimpan!")
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")
        else:
            st.warning("Perbaiki perbandingan terlebih dahulu sebelum menyimpan.")

    elif existing and existing.get("weights"):
        # Show previously saved weights
        st.markdown("<br>**Bobot yang Tersimpan Sebelumnya:**")
        for crit, w in zip(AHP_CRITERIA, existing["weights"]):
            label, _ = CRIT_LABELS[crit]
            bar_width = int(w * 300)
            bar_pct = int(w * 100)
            st.markdown(f"""
            <div class="weight-row">
                <div class="weight-label">{label}</div>
                <div class="weight-bar-bg">
                    <div class="weight-bar-fill" style="width:{bar_width}px"></div>
                </div>
                <div class="weight-pct">{bar_pct}%</div>
            </div>""", unsafe_allow_html=True)


# ── Radar chart (full width, below) ──────────────────────────────────────────
if "ahp_result" in st.session_state and st.session_state["ahp_result"]["is_valid"]:
    weights = st.session_state["ahp_result"]["weights"]
    labels = [CRIT_LABELS[c][0] for c in AHP_CRITERIA]

    st.markdown("---")
    st.markdown("### 📊 Visualisasi Distribusi Bobot")

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        fig = go.Figure(go.Scatterpolar(
            r=weights + [weights[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(124,58,237,0.2)",
            line=dict(color="#a78bfa", width=2.5),
            name="Bobot",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(weights)*1.3])),
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="#e2e8f0"),
            height=320, margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with fcol2:
        import plotly.express as px
        fig2 = px.bar(
            x=[CRIT_LABELS[c][0] for c in AHP_CRITERIA],
            y=[round(w * 100, 1) for w in weights],
            color=[round(w * 100, 1) for w in weights],
            color_continuous_scale="Purples",
            labels={"x": "Kriteria", "y": "Bobot (%)"},
        )
        fig2.update_layout(
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="#e2e8f0"),
            showlegend=False, coloraxis_showscale=False,
            height=320, margin=dict(t=20, b=20),
        )
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)
