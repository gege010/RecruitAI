"""
LLM Explainer — generates human-friendly, non-technical explanations for HR users.
Uses Groq API to write clear hiring recommendations.
"""
from __future__ import annotations

from groq import Groq
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import GROQ_API_KEY, GROQ_MODEL


_client: Groq | None = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


# ── Per-Candidate Explanation ─────────────────────────────────────────────────

_EXPLAIN_SYSTEM = """You are a senior HR consultant writing candidate assessments for a hiring manager.
Your goal is to write clear, human-friendly assessments in INDONESIAN language (Bahasa Indonesia).
The hiring manager is NOT a data scientist — they need plain, actionable language.
Do NOT mention algorithm names (SAW, WP, TOPSIS, MCDM, Borda, etc.) at all.
Write as if you personally reviewed this candidate's profile.
Be specific and reference the actual information provided."""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def generate_explanation(
    candidate_name: str,
    ensemble_rank: int,
    dimension_scores: dict[str, float],
    saw_score: float,
    wp_score: float,
    topsis_score: float,
    vacancy_title: str,
    vacancy_requirements: dict,
    candidate_profile: dict | None = None,
) -> str:
    """
    Generate a non-technical, HR-friendly explanation for a candidate's result.
    Returns Indonesian-language plain text.
    """

    # Build profile details if available
    profile_details = ""
    if candidate_profile:
        skills = candidate_profile.get("skills", [])
        certs = candidate_profile.get("certifications", [])
        education = candidate_profile.get("education", [])
        experience = candidate_profile.get("experience", [])

        if education:
            edu = education[0]
            profile_details += f"\nPendidikan: {edu.get('degree','')} {edu.get('field','')} dari {edu.get('institution','')}"
        if experience:
            total_months = sum(e.get("duration_months", 0) for e in experience)
            recent = experience[0]
            profile_details += f"\nPengalaman: {total_months} bulan total, terakhir sebagai {recent.get('title','')} di {recent.get('company','')}"
        if skills:
            profile_details += f"\nSkill utama: {', '.join(skills[:10])}"
        if certs:
            profile_details += f"\nSertifikasi: {', '.join(certs[:5])}"

    # Translate scores to plain-language levels
    def score_level(s: float) -> str:
        if s >= 0.8: return "sangat kuat"
        if s >= 0.6: return "cukup baik"
        if s >= 0.4: return "sedang"
        return "masih kurang"

    edu_level = score_level(dimension_scores.get("education", 0))
    exp_level = score_level(dimension_scores.get("experience", 0))
    skill_level = score_level(dimension_scores.get("skills", 0))
    cert_level = score_level(dimension_scores.get("certifications", 0))
    lang_level = score_level(dimension_scores.get("languages", 0))

    prompt = f"""Posisi yang dibuka: {vacancy_title}
Persyaratan utama: {', '.join(vacancy_requirements.get('required_skills', [])[:8])}
Minimal pengalaman: {vacancy_requirements.get('required_experience_months', 0)} bulan
Minimal pendidikan: {vacancy_requirements.get('required_education_level', 'S1')} bidang {vacancy_requirements.get('required_education_field', 'relevan')}

Nama Kandidat: {candidate_name}
Peringkat akhir: #{ensemble_rank}
{profile_details}

Penilaian sistem:
- Kesesuaian pendidikan: {edu_level} ({dimension_scores.get('education', 0):.0%})
- Kesesuaian pengalaman: {exp_level} ({dimension_scores.get('experience', 0):.0%})
- Kesesuaian skill: {skill_level} ({dimension_scores.get('skills', 0):.0%})
- Sertifikasi: {cert_level} ({dimension_scores.get('certifications', 0):.0%})
- Bahasa: {lang_level} ({dimension_scores.get('languages', 0):.0%})

Tulis asesmen kandidat ini dalam Bahasa Indonesia (3-4 kalimat):
1. Sebutkan kekuatan utama kandidat secara spesifik
2. Sebutkan kekurangan atau gap yang perlu diperhatikan (jika ada)
3. Berikan rekomendasi yang jelas: "Sangat direkomendasikan untuk interview" / "Direkomendasikan dengan catatan [...]" / "Belum direkomendasikan karena [...]"
Gunakan bahasa yang mudah dipahami dan profesional. Jangan sebut nama algoritma apapun."""

    try:
        resp = _get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _EXPLAIN_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("LLM explanation failed for {}: {}", candidate_name, exc)
        return f"Penilaian otomatis tidak tersedia untuk {candidate_name} (Peringkat #{ensemble_rank})."


# ── Executive Summary ─────────────────────────────────────────────────────────

def generate_summary_report(
    vacancy_title: str,
    ranked_results: list[dict],
    n_top: int = 3,
    vacancy_requirements: dict | None = None,
) -> str:
    """
    Generate an executive summary for the hiring manager (in Indonesian).
    Uses full candidate names and detailed scores for a specific, actionable output.
    """
    top = ranked_results[:n_top]

    def lvl(s: float) -> str:
        if s >= 0.8:  return "sangat kuat (≥80%)"
        if s >= 0.6:  return "baik (60–79%)"
        if s >= 0.4:  return "cukup (40–59%)"
        return f"lemah (<40%)"

    candidates_detail = []
    for r in top:
        name     = r.get("name", r.get("filename", "Unknown"))
        rank     = r.get("rank", r.get("ensemble_rank", "?"))
        edu      = float(r.get("education",      r.get("dimension_scores", {}).get("education", 0)))
        exp      = float(r.get("experience",     r.get("dimension_scores", {}).get("experience", 0)))
        skill    = float(r.get("skills",         r.get("dimension_scores", {}).get("skills", 0)))
        cert     = float(r.get("certifications", r.get("dimension_scores", {}).get("certifications", 0)))
        lang     = float(r.get("languages",      r.get("dimension_scores", {}).get("languages", 0)))
        overall  = float(r.get("overall", (edu+exp+skill+cert+lang)/5))

        detail = (
            f"Peringkat #{rank}: {name}\n"
            f"  - Kesesuaian keseluruhan: {overall:.0%}\n"
            f"  - Pendidikan: {lvl(edu)}\n"
            f"  - Pengalaman: {lvl(exp)}\n"
            f"  - Keahlian/Skill: {lvl(skill)}\n"
            f"  - Sertifikasi: {lvl(cert)}\n"
            f"  - Bahasa: {lvl(lang)}"
        )
        candidates_detail.append(detail)

    req_skills = ", ".join((vacancy_requirements or {}).get("required_skills", [])[:6]) or "—"
    min_exp    = (vacancy_requirements or {}).get("required_experience_months", 0)

    prompt = f"""Posisi yang dibuka: {vacancy_title}
Persyaratan skill utama: {req_skills}
Minimum pengalaman: {min_exp} bulan

Berikut hasil penilaian {len(top)} kandidat terbaik (berdasarkan sistem AI):

{chr(10).join(candidates_detail)}

Tulis ringkasan eksekutif dalam Bahasa Indonesia (4-5 kalimat) untuk manajer perekrutan:
1. Sebutkan nama kandidat terbaik secara spesifik dan alasannya (berdasarkan data di atas)
2. Bandingkan kandidat — siapa yang unggul di aspek apa?
3. Sebutkan jika ada kandidat yang sebaiknya TIDAK diprioritaskan dan mengapa
4. Rekomendasikan langkah konkret selanjutnya (misal: "Jadwalkan interview dengan [NAMA] minggu ini")

PENTING: Selalu sebut nama kandidat (bukan "kandidat #1"). Gunakan bahasa formal namun jelas dan langsung."""

    try:
        resp = _get_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Anda adalah konsultan HR senior yang menulis rekomendasi rekrutmen untuk direksi. Tulis dalam Bahasa Indonesia yang formal, spesifik, dan dapat langsung ditindaklanjuti."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=600,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("Summary report failed: {}", exc)
        return "Ringkasan eksekutif tidak dapat dibuat saat ini."


# ── Quick Fit Assessment (new) ────────────────────────────────────────────────

def generate_quick_fit(
    candidate_name: str,
    dimension_scores: dict[str, float],
    vacancy_title: str,
) -> str:
    """Generate a very short (1-line) fit summary for card display."""
    overall = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0
    if overall >= 0.75:
        return "✅ Sangat sesuai dengan posisi ini"
    elif overall >= 0.55:
        return "🟡 Cukup sesuai, perlu evaluasi lebih lanjut"
    elif overall >= 0.35:
        return "🟠 Kurang sesuai di beberapa aspek penting"
    else:
        return "🔴 Belum memenuhi sebagian besar persyaratan"
