"""
Page 1 — Kelola Lowongan Pekerjaan
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import streamlit as st
import json

from data.job_templates import get_template, list_job_families
from db.repositories import create_vacancy, list_vacancies, update_vacancy, delete_vacancy

st.set_page_config(page_title="Kelola Lowongan · RecruitAI", page_icon="💼", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #0f172a, #1e3a5f);
    border-radius: 14px; padding: 1.5rem 2rem; margin-bottom: 1.8rem;
    border-left: 5px solid #60a5fa;
}
.page-header h2 { color: #e2e8f0; margin: 0; font-size: 1.5rem; }
.page-header p  { color: #64748b; margin: 0.3rem 0 0; font-size: 0.9rem; }
.vacancy-card {
    background: #1e293b;
    border: 1px solid rgba(100,116,139,0.3);
    border-radius: 12px; padding: 1.2rem 1.4rem; margin-bottom: 0.8rem;
    transition: border-color 0.2s;
}
.vacancy-card:hover { border-color: #60a5fa; }
.vacancy-title { color: #e2e8f0; font-size: 1.05rem; font-weight: 700; margin: 0 0 0.4rem; }
.tag {
    background: #1e3a5f; color: #93c5fd;
    padding: 2px 10px; border-radius: 99px; font-size: 0.74rem;
    display: inline-block; margin: 2px;
}
.edit-form {
    background: #0f172a; border: 1px solid rgba(167,139,250,0.3);
    border-radius: 12px; padding: 1.5rem; margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="page-header">
  <h2>💼 Kelola Lowongan Pekerjaan</h2>
  <p>Buat dan edit lowongan dengan template siap pakai atau sesuaikan sendiri</p>
</div>""", unsafe_allow_html=True)


EDU_LEVELS = ["D3", "S1", "S2", "S3"]
EDU_LABELS = {"D3": "D3 / Diploma", "S1": "S1 / Sarjana", "S2": "S2 / Magister", "S3": "S3 / Doktoral"}

tab_create, tab_manage = st.tabs(["➕ Buat Lowongan Baru", "📋 Daftar Lowongan"])


# ── Tab 1: Buat ───────────────────────────────────────────────────────────────
with tab_create:
    st.markdown("#### Pilih Template Posisi")

    families = list_job_families()
    col_sel, col_load = st.columns([3, 1])
    with col_sel:
        selected_family = st.selectbox("Kategori Pekerjaan", families, key="new_family",
                                       help="Pilih kategori untuk mengisi otomatis persyaratan umum")
    with col_load:
        st.markdown("<br>", unsafe_allow_html=True)
        load_btn = st.button("📥 Muat Template", use_container_width=True)

    if load_btn or "template_loaded" not in st.session_state:
        st.session_state["template_data"] = get_template(selected_family)
        st.session_state["template_loaded"] = True

    tpl = st.session_state.get("template_data", get_template(selected_family))

    st.markdown("---")
    st.markdown("#### Detail Lowongan")

    col_a, col_b = st.columns(2)
    with col_a:
        v_title = st.text_input("Nama Posisi / Jabatan *",
                                value=tpl.get("job_family", ""),
                                placeholder="Contoh: Data Analyst, Software Engineer, HR Specialist")
        v_edu_level = st.selectbox(
            "Minimum Pendidikan",
            EDU_LEVELS,
            format_func=lambda x: EDU_LABELS.get(x, x),
            index=EDU_LEVELS.index(tpl.get("required_education_level", "S1"))
        )
        v_exp = st.number_input(
            "Minimum Pengalaman Kerja (bulan)",
            min_value=0, max_value=240,
            value=int(tpl.get("required_experience_months", 0)),
            help="Contoh: 12 = 1 tahun, 24 = 2 tahun"
        )
    with col_b:
        v_edu_field = st.text_input(
            "Bidang Studi yang Diinginkan",
            value=tpl.get("required_education_field", ""),
            placeholder="Contoh: Teknik Informatika, Manajemen, Akuntansi"
        )
        v_desc = st.text_area("Deskripsi Pekerjaan",
                              placeholder="Tuliskan tanggung jawab utama, lingkungan kerja, dll.",
                              height=120)

    st.markdown("#### Persyaratan Kandidat")
    st.caption("Masukkan satu item per baris. Semakin lengkap, semakin akurat analisis AI.")

    col_sk, col_cert, col_lang = st.columns(3)
    with col_sk:
        skills_default = "\n".join(tpl.get("required_skills", []))
        v_skills_raw = st.text_area("Skill yang Dibutuhkan",
                                    value=skills_default, height=180,
                                    placeholder="Python\nMachine Learning\nSQL\n...")
    with col_cert:
        certs_default = "\n".join(tpl.get("required_certifications", []))
        v_certs_raw = st.text_area("Sertifikasi (opsional)",
                                   value=certs_default, height=180,
                                   placeholder="AWS Certified\nGoogle Analytics\n...")
    with col_lang:
        langs_default = "\n".join(tpl.get("required_languages", []))
        v_langs_raw = st.text_area("Bahasa yang Dikuasai",
                                   value=langs_default, height=180,
                                   placeholder="Indonesia\nEnglish\n...")

    st.markdown("---")
    save_col, _ = st.columns([1, 4])
    with save_col:
        if st.button("💾 Simpan Lowongan", use_container_width=True, type="primary"):
            if not v_title.strip():
                st.error("Nama posisi harus diisi.")
            else:
                payload = {
                    "title": v_title.strip(),
                    "job_family": selected_family,
                    "description": v_desc.strip(),
                    "required_education_level": v_edu_level,
                    "required_education_field": v_edu_field.strip(),
                    "required_experience_months": int(v_exp),
                    "required_skills": [s.strip() for s in v_skills_raw.splitlines() if s.strip()],
                    "required_certifications": [c.strip() for c in v_certs_raw.splitlines() if c.strip()],
                    "required_languages": [l.strip() for l in v_langs_raw.splitlines() if l.strip()],
                }
                try:
                    rec = create_vacancy(payload)
                    st.success(f"✅ Lowongan **'{v_title}'** berhasil disimpan!")
                    st.session_state["template_loaded"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")


# ── Tab 2: Daftar & Edit ───────────────────────────────────────────────────────
with tab_manage:
    col_hdr, col_refresh = st.columns([5, 1])
    with col_hdr:
        st.markdown("#### Lowongan yang Sudah Dibuat")
    with col_refresh:
        if st.button("🔄 Refresh"):
            st.rerun()

    try:
        vacancies = list_vacancies()
    except Exception as e:
        st.error(f"Tidak dapat memuat data: {e}")
        vacancies = []

    if not vacancies:
        st.info("Belum ada lowongan. Buat lowongan baru di tab **'➕ Buat Lowongan Baru'**.")
    else:
        for v in vacancies:
            vid = v["id"]
            skills_preview = ", ".join((v.get("required_skills") or [])[:5])
            exp_text = f"{v.get('required_experience_months', 0)} bulan"
            edu_text = EDU_LABELS.get(v.get('required_education_level', 'S1'), 'S1')

            with st.container():
                col_info, col_btns = st.columns([6, 1])

                with col_info:
                    st.markdown(f"""
                    <div class="vacancy-card">
                        <div class="vacancy-title">💼 {v['title']}</div>
                        <span class="tag">📁 {v['job_family']}</span>
                        <span class="tag">🎓 Min. {edu_text}</span>
                        <span class="tag">⏱️ Min. {exp_text}</span>
                        <div style="margin-top:0.6rem; color:#64748b; font-size:0.83rem;">
                            <strong style="color:#94a3b8">Skill:</strong> {skills_preview or '—'}
                        </div>
                    </div>""", unsafe_allow_html=True)

                with col_btns:
                    st.markdown("<br>", unsafe_allow_html=True)
                    edit_key = f"edit_mode_{vid}"
                    if st.button("✏️ Edit", key=f"edit_btn_{vid}", use_container_width=True):
                        st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                    if st.button("🗑️ Hapus", key=f"del_{vid}", use_container_width=True):
                        try:
                            delete_vacancy(vid)
                            st.success("Lowongan dihapus.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                # ── Inline Edit Form ───────────────────────────────────────
                if st.session_state.get(f"edit_mode_{vid}", False):
                    with st.form(key=f"edit_form_{vid}"):
                        st.markdown('<div class="edit-form">', unsafe_allow_html=True)
                        st.markdown(f"**✏️ Edit Lowongan: {v['title']}**")

                        ec1, ec2 = st.columns(2)
                        with ec1:
                            new_title = st.text_input("Nama Posisi", value=v.get("title", ""), key=f"et_{vid}")
                            new_edu = st.selectbox("Min. Pendidikan", EDU_LEVELS,
                                                   format_func=lambda x: EDU_LABELS.get(x, x),
                                                   index=EDU_LEVELS.index(v.get("required_education_level", "S1")),
                                                   key=f"ee_{vid}")
                            new_exp = st.number_input("Min. Pengalaman (bulan)", 0, 240,
                                                      value=int(v.get("required_experience_months", 0)),
                                                      key=f"ex_{vid}")
                        with ec2:
                            new_field = st.text_input("Bidang Studi", value=v.get("required_education_field", ""), key=f"ef_{vid}")
                            new_desc = st.text_area("Deskripsi", value=v.get("description", ""), height=100, key=f"ed_{vid}")

                        ec3, ec4, ec5 = st.columns(3)
                        with ec3:
                            new_skills = st.text_area("Skill (1 per baris)",
                                                      value="\n".join(v.get("required_skills") or []),
                                                      height=120, key=f"esk_{vid}")
                        with ec4:
                            new_certs = st.text_area("Sertifikasi (1 per baris)",
                                                     value="\n".join(v.get("required_certifications") or []),
                                                     height=120, key=f"ec_{vid}")
                        with ec5:
                            new_langs = st.text_area("Bahasa (1 per baris)",
                                                     value="\n".join(v.get("required_languages") or []),
                                                     height=120, key=f"el_{vid}")

                        sb_col, cancel_col, _ = st.columns([1, 1, 3])
                        with sb_col:
                            submitted = st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True)
                        with cancel_col:
                            cancelled = st.form_submit_button("✖ Batal", use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        if submitted:
                            payload = {
                                "title": new_title.strip(),
                                "required_education_level": new_edu,
                                "required_education_field": new_field.strip(),
                                "required_experience_months": int(new_exp),
                                "description": new_desc.strip(),
                                "required_skills": [s.strip() for s in new_skills.splitlines() if s.strip()],
                                "required_certifications": [c.strip() for c in new_certs.splitlines() if c.strip()],
                                "required_languages": [l.strip() for l in new_langs.splitlines() if l.strip()],
                            }
                            try:
                                update_vacancy(vid, payload)
                                st.success("✅ Perubahan berhasil disimpan!")
                                st.session_state[f"edit_mode_{vid}"] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal menyimpan: {e}")

                        if cancelled:
                            st.session_state[f"edit_mode_{vid}"] = False
                            st.rerun()
