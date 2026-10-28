"""Evidence-based scoring. Rank is relative, never a hiring probability."""

import re
import pandas as pd
from core.mcdm.saw import run_saw
from core.mcdm.weighted_product import run_wp
from core.mcdm.topsis import run_topsis
from core.mcdm.ensemble import run_ensemble
from server.models import CRITERIA

LEVELS = {"SMA": 1, "D3": 2, "S1": 3, "S2": 4, "S3": 5}
ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "react.js": "react",
    "reactjs": "react",
    "node.js": "node",
    "nodejs": "node",
    "postgres": "postgresql",
    "bahasa indonesia": "indonesia",
    "indonesian": "indonesia",
    "english": "inggris",
}


def canonical(value):
    text = re.sub(r"\s+", " ", value.strip().casefold())
    return ALIASES.get(text, text)


def coverage(actual, required):
    values = {canonical(x) for x in actual}
    matched = [x for x in required if canonical(x) in values]
    missing = [x for x in required if canonical(x) not in values]
    return len(matched) / len(required) if required else 1.0, matched, missing


def dimensions(profile, job):
    edu = profile.get("education", "")
    req = job["required_education_level"]
    education = min(LEVELS.get(edu, 0) / LEVELS.get(req, 1), 1) if req else 1.0
    months = profile.get("experience_months")
    needed = job["required_experience_months"]
    experience = min((months or 0) / needed, 1) if needed else 1.0
    skills, matched, missing = coverage(
        profile.get("skills", []), job["required_skills"]
    )
    certs, _, missing_certs = coverage(
        profile.get("certifications", []), job["required_certifications"]
    )
    languages, _, missing_languages = coverage(
        profile.get("languages", []), job["required_languages"]
    )
    scores = dict(zip(CRITERIA, [education, experience, skills, certs, languages]))
    unknown = []
    if req and not edu:
        unknown.append("Pendidikan belum diverifikasi")
    if needed and months is None:
        unknown.append("Durasi pengalaman belum diverifikasi")
    if not profile.get("skills"):
        unknown.append("Keahlian belum diverifikasi")
    return scores, {
        "matched": matched,
        "missing": missing,
        "missing_certifications": missing_certs,
        "missing_languages": missing_languages,
        "unknown": unknown,
    }


def analyze(candidates, job):
    if not candidates:
        raise ValueError("Tambahkan kandidat sebelum menjalankan analisis.")
    rows, evidence = {}, {}
    for c in candidates:
        rows[c["id"]], evidence[c["id"]] = dimensions(c["profile"], job)
    matrix = pd.DataFrame.from_dict(rows, orient="index")[CRITERIA]
    weights = [job["weights"][key] / 100 for key in CRITERIA]
    ensemble = run_ensemble(
        {
            "saw": run_saw(matrix, weights),
            "wp": run_wp(matrix, weights),
            "topsis": run_topsis(matrix, weights),
        }
    )
    result = []
    for row in ensemble.to_dict("records"):
        cid = row.pop("candidate_id")
        dims = rows[cid]
        absolute = round(sum(dims[k] * job["weights"][k] for k in CRITERIA), 1)
        result.append(
            {
                "id": cid,
                "rank": int(row["ensemble_rank"]),
                "score": absolute,
                "dimensions": dims,
                "evidence": evidence[cid],
                "algorithms": row,
            }
        )
    return sorted(result, key=lambda r: (r["rank"], r["id"]))
