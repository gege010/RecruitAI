"""
Data-access layer — thin CRUD wrappers around Supabase REST.
All functions return plain Python dicts / lists for easy consumption.
"""
from __future__ import annotations

import uuid
from typing import Any

from loguru import logger

from db.supabase_client import get_supabase


# ── Job Vacancies ─────────────────────────────────────────────────────────────

def create_vacancy(data: dict) -> dict:
    res = get_supabase().table("job_vacancies").insert(data).execute()
    return res.data[0]


def get_vacancy(vacancy_id: str) -> dict | None:
    res = (
        get_supabase()
        .table("job_vacancies")
        .select("*")
        .eq("id", vacancy_id)
        .single()
        .execute()
    )
    return res.data


def list_vacancies() -> list[dict]:
    res = (
        get_supabase()
        .table("job_vacancies")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def update_vacancy(vacancy_id: str, data: dict) -> dict:
    res = (
        get_supabase()
        .table("job_vacancies")
        .update(data)
        .eq("id", vacancy_id)
        .execute()
    )
    return res.data[0]


def delete_vacancy(vacancy_id: str) -> None:
    get_supabase().table("job_vacancies").delete().eq("id", vacancy_id).execute()


# ── AHP Matrices ──────────────────────────────────────────────────────────────

def save_ahp_matrix(data: dict) -> dict:
    # Upsert: one AHP matrix per vacancy
    existing = (
        get_supabase()
        .table("ahp_matrices")
        .select("id")
        .eq("vacancy_id", data["vacancy_id"])
        .execute()
    )
    if existing.data:
        res = (
            get_supabase()
            .table("ahp_matrices")
            .update(data)
            .eq("vacancy_id", data["vacancy_id"])
            .execute()
        )
    else:
        res = get_supabase().table("ahp_matrices").insert(data).execute()
    return res.data[0]


def get_ahp_matrix(vacancy_id: str) -> dict | None:
    res = (
        get_supabase()
        .table("ahp_matrices")
        .select("*")
        .eq("vacancy_id", vacancy_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# ── Candidates ────────────────────────────────────────────────────────────────

def create_candidate(data: dict) -> dict:
    res = get_supabase().table("candidates").insert(data).execute()
    return res.data[0]


def update_candidate(candidate_id: str, data: dict) -> dict:
    res = (
        get_supabase()
        .table("candidates")
        .update(data)
        .eq("id", candidate_id)
        .execute()
    )
    return res.data[0]


def list_candidates(vacancy_id: str) -> list[dict]:
    res = (
        get_supabase()
        .table("candidates")
        .select("*")
        .eq("vacancy_id", vacancy_id)
        .order("created_at")
        .execute()
    )
    return res.data or []


def delete_candidate(candidate_id: str) -> None:
    get_supabase().table("candidates").delete().eq("id", candidate_id).execute()


# ── Scoring Results ───────────────────────────────────────────────────────────

def upsert_scoring_result(data: dict) -> dict:
    res = (
        get_supabase()
        .table("scoring_results")
        .upsert(data, on_conflict="vacancy_id,candidate_id")
        .execute()
    )
    return res.data[0]


def get_scoring_results(vacancy_id: str) -> list[dict]:
    """Return results with candidate info joined."""
    res = (
        get_supabase()
        .table("scoring_results")
        .select("*, candidates(original_filename, parsed_profile)")
        .eq("vacancy_id", vacancy_id)
        .order("ensemble_rank")
        .execute()
    )
    return res.data or []


def delete_scoring_results(vacancy_id: str) -> None:
    get_supabase().table("scoring_results").delete().eq("vacancy_id", vacancy_id).execute()
