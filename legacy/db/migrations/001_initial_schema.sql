-- ============================================================
-- Resume Auto-Selection DSS — Initial Database Schema
-- Supabase (PostgreSQL)
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── 1. Job Vacancies ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_vacancies (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title                    TEXT NOT NULL,
    job_family               TEXT NOT NULL,
    description              TEXT,
    required_education_level TEXT,          -- "S1", "S2", "S3", "D3"
    required_education_field TEXT,          -- e.g. "Computer Science"
    required_experience_months INT DEFAULT 0,
    required_skills          JSONB DEFAULT '[]',
    required_certifications  JSONB DEFAULT '[]',
    required_languages       JSONB DEFAULT '[]',
    ahp_weights              JSONB,         -- cached after AHP wizard
    created_at               TIMESTAMPTZ DEFAULT now(),
    updated_at               TIMESTAMPTZ DEFAULT now()
);

-- ── 2. AHP Matrices ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ahp_matrices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vacancy_id          UUID REFERENCES job_vacancies(id) ON DELETE CASCADE,
    criteria_names      JSONB NOT NULL,     -- ["Education","Experience","Skills","Certifications","Languages"]
    pairwise_matrix     JSONB NOT NULL,     -- 2D array (n×n)
    weights             JSONB,              -- derived priority vector
    lambda_max          FLOAT,
    consistency_index   FLOAT,
    consistency_ratio   FLOAT,
    is_valid            BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- ── 3. Candidates ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidates (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vacancy_id        UUID REFERENCES job_vacancies(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    raw_text          TEXT,
    parsed_profile    JSONB,               -- full structured extraction from LLM
    parsing_status    TEXT DEFAULT 'pending',  -- pending | success | failed
    parsing_error     TEXT,
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- ── 4. Scoring Results ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS scoring_results (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vacancy_id        UUID REFERENCES job_vacancies(id) ON DELETE CASCADE,
    candidate_id      UUID REFERENCES candidates(id) ON DELETE CASCADE,
    dimension_scores  JSONB,              -- {education, experience, skills, certifications, languages}
    normalized_scores JSONB,             -- normalized values used in MCDM
    saw_score         FLOAT,
    saw_rank          INT,
    wp_score          FLOAT,
    wp_rank           INT,
    topsis_score      FLOAT,
    topsis_rank       INT,
    borda_score       INT,               -- sum of ranks (lower = better)
    ensemble_rank     INT,               -- final rank
    ai_explanation    TEXT,
    computed_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(vacancy_id, candidate_id)
);

-- ── Indexes ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_candidates_vacancy ON candidates(vacancy_id);
CREATE INDEX IF NOT EXISTS idx_scoring_vacancy ON scoring_results(vacancy_id);
CREATE INDEX IF NOT EXISTS idx_scoring_rank ON scoring_results(vacancy_id, ensemble_rank);

-- ── Auto-update updated_at ───────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_job_vacancies_updated_at
    BEFORE UPDATE ON job_vacancies
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
