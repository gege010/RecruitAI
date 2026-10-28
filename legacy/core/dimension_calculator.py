"""
Dimension Calculator — converts a CandidateProfile into 5 numeric scores [0, 1].

Dimensions:
  1. education      — degree level + field relevance
  2. experience     — total months + role relevance
  3. skills         — semantic skill overlap
  4. certifications — keyword + semantic match
  5. languages      — requirement fulfillment ratio
"""
from __future__ import annotations

import math
from app.config import EDUCATION_LEVEL_SCORES
from core.resume_parser import CandidateProfile
from core.semantic_scorer import skill_match_score, text_relevance_score


# ── Education ─────────────────────────────────────────────────────────────────

def _education_score(
    profile: CandidateProfile,
    required_level: str,
    required_field: str,
) -> float:
    if not profile.education:
        return 0.0

    best = 0.0
    for edu in profile.education:
        level_score = _match_edu_level(edu.degree, required_level)
        field_score = text_relevance_score(edu.field, required_field) if required_field else 1.0
        # Weighted combination: level 60%, field 40%
        combined = 0.6 * level_score + 0.4 * field_score
        best = max(best, combined)

    return round(best, 4)


def _match_edu_level(degree: str, required: str) -> float:
    """Map degree string to 0-1 score; penalise if below required."""
    degree_score = _lookup_level(degree)
    req_score    = _lookup_level(required)

    if req_score == 0:
        return degree_score       # no requirement → full credit

    # Reward meeting/exceeding, penalise falling short
    if degree_score >= req_score:
        return 1.0
    return degree_score / req_score


def _lookup_level(text: str) -> float:
    text_upper = text.upper()
    for key, val in EDUCATION_LEVEL_SCORES.items():
        if key.upper() in text_upper:
            return val
    return 0.3    # unknown → partial credit


# ── Experience ────────────────────────────────────────────────────────────────

def _experience_score(
    profile: CandidateProfile,
    required_months: int,
    job_title: str,
) -> float:
    if not profile.experience:
        return 0.0

    total_months = sum(e.duration_months for e in profile.experience)

    # Quantity score: sigmoid-style, saturates at 2× requirement
    if required_months > 0:
        ratio = total_months / required_months
        qty_score = min(ratio, 2.0) / 2.0      # cap at 1.0 when ≥2× requirement
    else:
        qty_score = min(total_months / 24, 1.0)

    # Relevance: semantic match of latest role title to job
    if job_title:
        titles = " ".join(e.title for e in profile.experience)
        rel_score = text_relevance_score(titles, job_title)
    else:
        rel_score = 1.0

    return round(0.6 * qty_score + 0.4 * rel_score, 4)


# ── Skills ────────────────────────────────────────────────────────────────────

def _skills_score(profile: CandidateProfile, required_skills: list[str]) -> float:
    return round(skill_match_score(profile.skills, required_skills), 4)


# ── Certifications ────────────────────────────────────────────────────────────

def _certifications_score(
    profile: CandidateProfile,
    required_certs: list[str],
) -> float:
    if not required_certs:
        return 1.0
    if not profile.certifications:
        return 0.0
    return round(skill_match_score(profile.certifications, required_certs), 4)


# ── Languages ─────────────────────────────────────────────────────────────────

def _languages_score(
    profile: CandidateProfile,
    required_languages: list[str],
) -> float:
    if not required_languages:
        return 1.0
    if not profile.languages:
        return 0.0

    candidate_langs_lower = {l.lower() for l in profile.languages}
    matched = sum(
        1 for req in required_languages
        if req.lower() in candidate_langs_lower
    )
    return round(matched / len(required_languages), 4)


# ── Public API ────────────────────────────────────────────────────────────────

def compute_dimensions(
    profile: CandidateProfile,
    vacancy: dict,
) -> dict[str, float]:
    """
    Compute all 5 scoring dimensions for a candidate given a job vacancy.

    Args:
        profile:  parsed CandidateProfile
        vacancy:  dict from job_vacancies table

    Returns:
        dict {education, experience, skills, certifications, languages} ∈ [0,1]
    """
    return {
        "education": _education_score(
            profile,
            required_level=vacancy.get("required_education_level", "S1"),
            required_field=vacancy.get("required_education_field", ""),
        ),
        "experience": _experience_score(
            profile,
            required_months=int(vacancy.get("required_experience_months", 0)),
            job_title=vacancy.get("title", ""),
        ),
        "skills": _skills_score(
            profile,
            required_skills=vacancy.get("required_skills", []),
        ),
        "certifications": _certifications_score(
            profile,
            required_certs=vacancy.get("required_certifications", []),
        ),
        "languages": _languages_score(
            profile,
            required_languages=vacancy.get("required_languages", []),
        ),
    }
