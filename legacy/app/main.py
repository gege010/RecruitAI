"""
Resume Auto-Selection DSS — Streamlit Home Page
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Sistem Seleksi Kandidat",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS (juga mempercantik sidebar) ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ─── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 60%, #0f172a 100%);
    border-right: 1px solid rgba(167,139,250,0.2);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stMarkdown a {
    color: #a78bfa !important;
    text-decoration: none;
}
[data-testid="stSidebarNav"] { gap: 0 !important; padding-top: 0.5rem; }
[data-testid="stSidebarNav"] li {
    padding: 0;
}
[data-testid="stSidebarNav"] a {
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    margin: 2px 8px;
    transition: background 0.2s;
    font-size: 0.9rem;
    font-weight: 500;
}
[data-testid="stSidebarNav"] a:hover {
    background: rgba(167,139,250,0.15) !important;
    color: #a78bfa !important;
}
[data-testid="stSidebarNav"] [aria-selected="true"] {
    background: rgba(167,139,250,0.25) !important;
    color: #a78bfa !important;
    font-weight: 600;
}

/* ─── Main content ────────────────────────────────────────── */
.main .block-container { padding-top: 2rem; padding-bottom: 2rem; }

.hero {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
    border-radius: 20px;
    padding: 3rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 20px 60px rgba(124,58,237,0.35);
    position: relative; overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute; top: -50%; right: -10%;
    width: 400px; height: 400px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}
.hero h1 { color: white; font-size: 2.4rem; font-weight: 800; margin: 0; }
.hero p  { color: rgba(255,255,255,0.85); font-size: 1.05rem; margin: 0.6rem 0 0; }

.stat-card {
    background: #1e293b;
    border: 1px solid rgba(100,116,139,0.3);
    border-radius: 14px;
    padding: 1.4rem 1.2rem;
    text-align: center;
}
.stat-card .num { font-size: 2.2rem; font-weight: 800; color: #a78bfa; }
.stat-card .lbl { font-size: 0.8rem; color: #64748b; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.05em; }

.step-card {
    background: #1e293b;
    border: 1px solid rgba(100,116,139,0.25);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    display: flex; gap: 1rem; align-items: flex-start;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}
.step-card:hover { border-color: #a78bfa; }
.step-num {
    background: linear-gradient(135deg, #4f46e5, #a855f7);
    color: white; font-weight: 800;
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 0.9rem;
}
.step-content h4 { color: #e2e8f0; margin: 0 0 0.2rem; font-size: 0.95rem; }
.step-content p  { color: #64748b; margin: 0; font-size: 0.83rem; }

.badge-ok  { background:#064e3b; color:#34d399; padding:3px 12px; border-radius:99px; font-size:0.82rem; font-weight: 600; }
.badge-err { background:#7f1d1d; color:#f87171; padding:3px 12px; border-radius:99px; font-size:0.82rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar brand ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 1.2rem 0.5rem; border-bottom: 1px solid rgba(167,139,250,0.2); margin-bottom: 0.5rem;">
        <div style="font-size: 1.3rem; font-weight: 800; color: #a78bfa;">🧠 RecruitAI</div>
        <div style="font-size: 0.72rem; color: #475569; margin-top: 2px;">Sistem Seleksi Kandidat Berbasis AI</div>
    </div>
    <div style="padding: 0.4rem 1.2rem; font-size: 0.7rem; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-top: 0.3rem;">
    Menu Utama
    </div>
    """, unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🧠 Sistem Seleksi Kandidat Berbasis AI</h1>
  <p>Upload CV kandidat, tentukan bobot kriteria, dan dapatkan peringkat otomatis yang objektif dan transparan</p>
</div>
""", unsafe_allow_html=True)


# ── DB Status + Metrics ───────────────────────────────────────────────────────
col_status, _ = st.columns([1, 4])
with col_status:
    with st.spinner("Memeriksa koneksi..."):
        try:
            from db.supabase_client import check_connection
            ok = check_connection()
            badge = '<span class="badge-ok">● Terhubung ke Database</span>' if ok else \
                    '<span class="badge-err">● Database Tidak Terhubung</span>'
        except Exception:
            badge = '<span class="badge-err">● Database Belum Dikonfigurasi</span>'
    st.markdown(badge, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Live metrics
try:
    from db.repositories import list_vacancies, list_candidates
    vacancies = list_vacancies()
    n_vacancies = len(vacancies)
    n_candidates = 0
    n_parsed = 0
    for v in vacancies:
        try:
            cands = list_candidates(v["id"])
            n_candidates += len(cands)
            n_parsed += sum(1 for c in cands if c.get("parsing_status") == "success")
        except Exception:
            pass
except Exception:
    n_vacancies = n_candidates = n_parsed = 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="stat-card"><div class="num">{n_vacancies}</div><div class="lbl">Lowongan Aktif</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><div class="num">{n_candidates}</div><div class="lbl">Total Kandidat</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-card"><div class="num">{n_parsed}</div><div class="lbl">CV Diproses</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="stat-card"><div class="num">AI</div><div class="lbl">Analisis Otomatis</div></div>', unsafe_allow_html=True)


# ── Quick Start ───────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📋 Cara Menggunakan Sistem")

steps = [
    ("1", "Buat Lowongan Pekerjaan",
     "Pilih kategori pekerjaan → isi detail posisi dan persyaratan (skill, pendidikan, pengalaman).",
     "💼 Kelola Lowongan"),
    ("2", "Upload CV Kandidat",
     "Upload file PDF CV kandidat. Sistem AI akan membaca dan mengekstrak informasi secara otomatis.",
     "📄 Upload CV"),
    ("3", "Atur Prioritas Kriteria",
     "Tentukan seberapa penting masing-masing kriteria (pendidikan, pengalaman, skill, dll.) untuk posisi ini.",
     "⚖️ Atur Prioritas"),
    ("4", "Jalankan Analisis",
     "Klik satu tombol untuk menjalankan analisis AI terhadap semua kandidat secara bersamaan.",
     "🚀 Jalankan Analisis"),
    ("5", "Lihat Hasil & Rekomendasi",
     "Dapatkan peringkat kandidat disertai penjelasan dan rekomendasi yang mudah dipahami.",
     "📊 Lihat Hasil"),
]

for num, title, desc, page in steps:
    st.markdown(f"""
    <div class="step-card">
        <div class="step-num">{num}</div>
        <div class="step-content">
            <h4>{title} — <span style="color:#64748b;font-weight:400">{page}</span></h4>
            <p>{desc}</p>
        </div>
    </div>""", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<center style='color:#1e293b;font-size:0.78rem'>Resume Auto-Selection DSS · Universitas Brawijaya · Fakultas Ilmu Komputer · 2026</center>",
    unsafe_allow_html=True,
)
