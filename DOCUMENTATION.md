# 📚 Dokumentasi Teknis — RecruitAI

> Sistem Pendukung Keputusan Seleksi Kandidat Berbasis AI  
> Universitas Brawijaya · Fakultas Ilmu Komputer · 2026

---

## 1. Deskripsi Proyek

**RecruitAI** adalah aplikasi web berbasis kecerdasan buatan yang dirancang untuk membantu tim Human Resources (HR) dalam melakukan proses seleksi kandidat secara **objektif, transparan, dan efisien**. Sistem ini mengeliminasi bias subjektif dalam proses rekrutmen dengan menggabungkan dua pendekatan utama:

1. **AI Generatif** — Membaca dan mengekstrak informasi dari CV kandidat secara otomatis, termasuk CV yang berupa gambar/scan.
2. **Multi-Criteria Decision Making (MCDM)** — Membandingkan kandidat berdasarkan beberapa kriteria sekaligus menggunakan tiga algoritma berbeda yang hasilnya digabungkan (*ensemble*).

### Latar Belakang

Proses seleksi CV secara manual memiliki beberapa kelemahan:
- **Lambat** — Membaca puluhan hingga ratusan CV membutuhkan waktu berjam-jam
- **Subjektif** — Keputusan dapat dipengaruhi bias pribadi recruiter
- **Tidak konsisten** — Standar penilaian bisa berubah antar sesi review
- **Tidak terdokumentasi** — Alasan penolakan/penerimaan sulit dilacak

RecruitAI menyelesaikan semua masalah di atas dalam satu sistem terpadu.

---

## 2. Fitur Utama

| # | Fitur | Deskripsi |
|---|---|---|
| 1 | **Manajemen Lowongan** | Buat, edit, dan hapus lowongan. Tersedia 10+ template kategori pekerjaan (Data Science, Software Engineering, Finance, dll.) |
| 2 | **Upload CV Multi-File** | Upload banyak file PDF sekaligus. Sistem memproses semua secara batch |
| 3 | **AI Parsing Otomatis** | LLM membaca dan mengekstrak: nama, email, pendidikan, pengalaman kerja, skill, sertifikasi, bahasa |
| 4 | **OCR via Groq Vision** | CV yang berupa gambar/scan (image-based PDF) diproses menggunakan Vision AI tanpa instalasi binary tambahan |
| 5 | **Wizard Prioritas Kriteria** | Interface intuitif untuk menentukan bobot tiap kriteria menggunakan metode AHP dengan validasi konsistensi otomatis |
| 6 | **Analisis Multi-Kriteria** | Tiga algoritma (SAW, WP, TOPSIS) berjalan paralel dan hasilnya digabung dengan Borda Count |
| 7 | **Dashboard Hasil HR-Friendly** | Peringkat kandidat dengan skor bar, badge kesesuaian, dan penjelasan AI dalam Bahasa Indonesia |
| 8 | **Penjelasan AI per Kandidat** | Setiap kandidat mendapat ulasan naratif spesifik: kekuatan, kelemahan, dan rekomendasi |
| 9 | **Ringkasan Eksekutif AI** | Satu paragraf rekomendasi untuk manajer yang menyebut nama kandidat secara eksplisit |
| 10 | **Perbandingan Visual** | Radar chart yang membandingkan profil antar kandidat secara side-by-side |
| 11 | **Ekspor Laporan** | Unduh hasil seleksi dalam format Excel (.xlsx) atau CSV |
| 12 | **Edit Lowongan** | Edit semua detail lowongan yang sudah ada langsung dari halaman daftar |

---

## 3. Alur Sistem (End-to-End)

```
┌─────────────────────────────────────────────────────────────────┐
│                        PENGGUNA (HR)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────▼──────────────────┐
          │      LANGKAH 1: Buat Lowongan       │
          │  • Pilih kategori (template)         │
          │  • Isi persyaratan: skill, edu,      │
          │    pengalaman, sertifikasi, bahasa   │
          └─────────────────┬──────────────────┘
                            │ simpan ke Supabase
          ┌─────────────────▼──────────────────┐
          │      LANGKAH 2: Upload CV           │
          │  • Upload PDF (1 atau banyak)        │
          │  • Pipeline ekstraksi 3-strategi:    │
          │    pdfplumber → PyMuPDF → Groq Vision│
          │  • LLM parse → JSON terstruktur     │
          └─────────────────┬──────────────────┘
                            │ simpan profil ke Supabase
          ┌─────────────────▼──────────────────┐
          │      LANGKAH 3: Atur Prioritas      │
          │  • Bandingkan 5 kriteria berpasangan │
          │  • Validasi Consistency Ratio < 0.10 │
          │  • Hitung bobot w₁...w₅             │
          └─────────────────┬──────────────────┘
                            │ simpan bobot AHP ke Supabase
          ┌─────────────────▼──────────────────┐
          │      LANGKAH 4: Jalankan Analisis   │
          │  • Hitung 5 dimensi skor [0,1]      │
          │  • Bangun decision matrix            │
          │  • SAW + WP + TOPSIS                │
          │  • Borda Count ensemble              │
          │  • Generate penjelasan AI            │
          └─────────────────┬──────────────────┘
                            │ simpan hasil ke Supabase
          ┌─────────────────▼──────────────────┐
          │      LANGKAH 5: Lihat Hasil         │
          │  • Peringkat + skor bar per kriteria │
          │  • Badge kesesuaian (✅ 🟡 🟠 🔴)   │
          │  • Penjelasan AI per kandidat        │
          │  • Ringkasan eksekutif               │
          │  • Radar chart perbandingan          │
          │  • Export Excel / CSV                │
          └────────────────────────────────────┘
```

---

## 4. Arsitektur Sistem

```
resume-auto-selection/
│
├── app/                          ← Streamlit UI layer
│   ├── main.py                   # Halaman beranda
│   ├── config.py                 # Konfigurasi global & konstanta
│   └── pages/
│       ├── 01_job_vacancies.py   # CRUD lowongan
│       ├── 02_upload_resumes.py  # Upload & parsing CV
│       ├── 03_ahp_wizard.py      # Wizard bobot kriteria
│       ├── 04_run_analysis.py    # Eksekusi pipeline MCDM
│       └── 05_results.py         # Dashboard hasil seleksi
│
├── core/                         ← Business logic layer
│   ├── resume_parser.py          # PDF → JSON (3-strategi)
│   ├── semantic_scorer.py        # Cosine similarity embeddings
│   ├── dimension_calculator.py   # Kalkulasi 5 dimensi [0,1]
│   ├── llm_explainer.py          # Generasi penjelasan AI (BI)
│   └── mcdm/
│       ├── ahp.py                # AHP + CR validation
│       ├── saw.py                # Simple Additive Weighting
│       ├── weighted_product.py   # Weighted Product
│       ├── topsis.py             # TOPSIS
│       └── ensemble.py           # Borda Count aggregation
│
├── db/                           ← Data access layer
│   ├── supabase_client.py        # Singleton koneksi
│   ├── repositories.py           # CRUD semua entitas
│   └── migrations/
│       └── 001_initial_schema.sql
│
├── data/
│   └── job_templates.py          # 10+ template lowongan
│
└── .streamlit/
    └── config.toml               # Tema dark + server config
```

### Pola Desain

- **Thin Repository Pattern** — UI tidak berinteraksi langsung dengan Supabase; semua query melalui `db/repositories.py`
- **Lazy Loading** — Model embedding (`sentence-transformers`) hanya dimuat saat pertama kali dibutuhkan
- **Strategy Pattern** — PDF extraction menggunakan 3 strategi dengan fallback otomatis
- **Singleton** — Koneksi Supabase dan model embedding di-cache untuk efisiensi

---

## 5. Mekanisme: Pipeline Parsing CV

### 5.1 Ekstraksi Teks (3-Strategi)

Sistem mencoba tiga metode secara berurutan, berhenti saat berhasil:

```
PDF Bytes
    │
    ├─► [Strategi 1] pdfplumber — word-based extraction
    │       Ambil semua kata dengan koordinat posisi (x, top)
    │       Rekonstruksi baris berdasarkan posisi Y
    │       → Jika menghasilkan > 100 karakter: SELESAI
    │
    ├─► [Strategi 2] PyMuPDF (fitz) — layout extraction
    │       Lebih baik untuk PDF dengan layout kompleks,
    │       kolom ganda, atau tabel
    │       → Jika menghasilkan > 100 karakter: SELESAI
    │
    └─► [Strategi 3] Groq Vision API — OCR berbasis AI
            Render setiap halaman PDF menjadi gambar PNG (200 DPI)
            Encode ke base64
            Kirim ke model llama-4-scout-17b (vision)
            → Untuk PDF scan/gambar, maks 4 halaman
```

### 5.2 Strukturisasi dengan LLM

Teks mentah dikirim ke Groq API (`llama-3.3-70b-versatile`) dengan sistem prompt yang meminta output JSON ketat:

```json
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "summary": "string",
  "education": [
    {
      "degree": "S1/S2/Bachelor/...",
      "field": "bidang studi",
      "institution": "nama universitas",
      "gpa": null,
      "graduation_year": 2020
    }
  ],
  "experience": [
    {
      "title": "jabatan",
      "company": "perusahaan",
      "duration_months": 24,
      "description": "tanggung jawab",
      "is_current": false
    }
  ],
  "skills": ["Python", "SQL", ...],
  "certifications": ["AWS Certified", ...],
  "languages": ["Indonesia", "English"]
}
```

**Parameter LLM:**
- Temperature: `0.05` (sangat deterministik)
- Max tokens: `4096` (profil detail)
- Retry: 3x dengan exponential backoff

### 5.3 Post-Processing

- Deduplikasi skill (case-insensitive)
- Normalisasi bahasa (title case)
- Cap `duration_months` maksimum 480 bulan
- Partial construction jika validasi Pydantic gagal

---

## 6. Mekanisme: Kalkulasi Dimensi

Setiap kandidat dinilai pada **5 dimensi**, masing-masing menghasilkan skor `[0.0, 1.0]`:

### 6.1 Dimensi Pendidikan

```
skor = 0.6 × level_score + 0.4 × field_score

level_score:
  Jika degree_candidate ≥ degree_required → 1.0
  Jika kurang                             → degree_score / required_score

  Mapping level:
  S3/PhD = 1.0 | S2/Master = 0.8 | S1/Bachelor = 0.6
  D4 = 0.55    | D3 = 0.45        | SMA/SMK = 0.15

field_score:
  cosine_similarity(embed(bidang_kandidat), embed(dbidang_required))
```

### 6.2 Dimensi Pengalaman

```
skor = 0.6 × qty_score + 0.4 × relevance_score

qty_score:
  ratio = total_bulan / bulan_required
  qty_score = min(ratio, 2.0) / 2.0   ← cap di 1.0 jika ≥ 2× requirement

relevance_score:
  cosine_similarity(embed(semua_jabatan), embed(title_lowongan))
```

### 6.3 Dimensi Keahlian (Skill)

```
Untuk setiap required skill r:
  max_sim(r) = max cosine_similarity(embed(r), embed(cand_skill_i))
               untuk semua skill kandidat i

skor = mean(max_sim(r)) untuk semua r
```

Strategi ini memastikan skill yang serupa (misal "ML" ≈ "Machine Learning") tetap terdeteksi.

### 6.4 Dimensi Sertifikasi

```
Jika tidak ada required_certs → skor = 1.0 (tidak diwajibkan)
Jika kandidat tidak punya cert → skor = 0.0

skor = skill_match_score(candidate_certs, required_certs)
       (sama dengan strategi semantic matching di atas)
```

### 6.5 Dimensi Bahasa

```
Exact match (case-insensitive):
matched = jumlah bahasa required yang ada di profil kandidat
skor = matched / total_required
```

---

## 7. Mekanisme: AHP (Analytic Hierarchy Process)

AHP digunakan untuk menentukan **bobot kepentingan** tiap kriteria secara matematis dan konsisten.

### 7.1 Input

Pengguna melakukan **perbandingan berpasangan** antara 5 kriteria menggunakan skala Saaty 1–9. Dengan 5 kriteria, terdapat C(5,2) = **10 pasang perbandingan**.

### 7.2 Proses

```
1. Bangun matriks A (5×5) yang resiprokal:
   A[i][j] = nilai_user   →  A[j][i] = 1 / nilai_user
   A[i][i] = 1.0 (diagonal)

2. Normalisasi tiap kolom:
   A_norm[i][j] = A[i][j] / sum(kolom_j)

3. Hitung Priority Vector (bobot):
   w[i] = mean(baris_i dari A_norm)
   → w dijumlahkan = 1.0

4. Uji konsistensi:
   λ_max = mean(A × w / w)
   CI    = (λ_max - n) / (n - 1)
   CR    = CI / RI[n]   ← RI[5] = 1.12

5. Validasi: CR < 0.10 ✓
```

### 7.3 Random Index (RI) — Saaty 1980

| n | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| RI | 0.00 | 0.00 | 0.58 | 0.90 | **1.12** | 1.24 | 1.32 |

Jika CR ≥ 0.10, pengguna diminta merevisi perbandingan hingga konsisten.

---

## 8. Mekanisme: Algoritma MCDM

### 8.1 Decision Matrix

Sebelum algoritma dijalankan, dibentuk matriks keputusan D (m × n):
- m = jumlah kandidat
- n = 5 (jumlah kriteria)
- Nilai = skor dimensi [0,1]

### 8.2 SAW (Simple Additive Weighting)

```
V_i = Σ (w_j × r_ij)

r_ij = d_ij / max(d_j)    ← normalisasi benefit

Kandidat dengan V terbesar = terbaik
```

### 8.3 WP (Weighted Product)

```
S_i = Π (d_ij ^ w_j)

Kandidat dengan S terbesar = terbaik

Karakteristik: penalti lebih besar untuk nilai sangat rendah di satu kriteria
```

### 8.4 TOPSIS

```
1. Normalisasi: r_ij = d_ij / sqrt(Σ d_kj²)
2. Bobot: v_ij = w_j × r_ij
3. Solusi ideal positif: A⁺ = max(v_ij) per kriteria
4. Solusi ideal negatif: A⁻ = min(v_ij) per kriteria
5. Jarak: d⁺_i = sqrt(Σ(v_ij - A⁺_j)²)
           d⁻_i = sqrt(Σ(v_ij - A⁻_j)²)
6. Skor: C_i = d⁻_i / (d⁺_i + d⁻_i)

C_i mendekati 1 = kandidat terbaik
```

### 8.5 Borda Count Ensemble

```
Setiap algoritma memberikan rank ordinal per kandidat:
  SAW_rank[i], WP_rank[i], TOPSIS_rank[i]

Borda_score[i] = SAW_rank[i] + WP_rank[i] + TOPSIS_rank[i]

Final_rank = rank ascending dari Borda_score
(Borda_score terkecil = peringkat 1 = terbaik)
```

Pendekatan ensemble mengurangi bias dari satu algoritma tunggal dan menghasilkan peringkat yang lebih robust.

---

## 9. Mekanisme: AI Explanation

### 9.1 Per-Kandidat

Setiap kandidat mendapat ulasan naratif yang di-generate oleh LLM (`llama-3.3-70b-versatile`) dengan konteks:

- Nama kandidat
- Peringkat akhir
- Skor tiap dimensi (dengan label level: "sangat kuat ≥80%", "baik 60-79%", dll.)
- Detail profil (pendidikan, pengalaman terakhir, skill utama)
- Persyaratan lowongan

**Output yang diharapkan:** 3–4 kalimat Bahasa Indonesia yang menyebutkan kekuatan spesifik, gap, dan rekomendasi eksplisit (rekomendasikan/tidak).

### 9.2 Ringkasan Eksekutif

Dibuat atas permintaan pengguna, mencakup 3 kandidat teratas dengan detail skor lengkap. Prompt memaksa AI:
- Menyebut nama asli (bukan "#1" atau "kandidat pertama")
- Membandingkan antar kandidat secara spesifik
- Memberikan rekomendasi langkah konkret (misal: "Jadwalkan interview dengan [NAMA] minggu ini")

---

## 10. Skema Database

Sistem menggunakan **Supabase (PostgreSQL)** dengan tabel-tabel berikut:

### Tabel `job_vacancies`
```sql
id                        UUID PRIMARY KEY
title                     TEXT NOT NULL
job_family                TEXT
description               TEXT
required_education_level  TEXT   -- D3, S1, S2, S3
required_education_field  TEXT
required_experience_months INT
required_skills           TEXT[] -- array
required_certifications   TEXT[]
required_languages        TEXT[]
created_at                TIMESTAMPTZ
```

### Tabel `candidates`
```sql
id                UUID PRIMARY KEY
vacancy_id        UUID → job_vacancies(id)
original_filename TEXT
raw_text          TEXT
parsed_profile    JSONB  -- CandidateProfile JSON
parsing_status    TEXT   -- 'success' | 'failed' | 'pending'
parsing_error     TEXT
created_at        TIMESTAMPTZ
```

### Tabel `ahp_matrices`
```sql
id                 UUID PRIMARY KEY
vacancy_id         UUID → job_vacancies(id)
criteria_names     TEXT[]
pairwise_matrix    JSONB  -- n×n matrix
weights            FLOAT[]
lambda_max         FLOAT
consistency_index  FLOAT
consistency_ratio  FLOAT
is_valid           BOOLEAN
created_at         TIMESTAMPTZ
```

### Tabel `scoring_results`
```sql
id               UUID PRIMARY KEY
vacancy_id       UUID → job_vacancies(id)
candidate_id     UUID → candidates(id)
dimension_scores JSONB   -- {education, experience, skills, ...}
normalized_scores JSONB
saw_score        FLOAT
saw_rank         INT
wp_score         FLOAT
wp_rank          INT
topsis_score     FLOAT
topsis_rank      INT
borda_score      INT
ensemble_rank    INT
ai_explanation   TEXT
created_at       TIMESTAMPTZ
```

---

## 11. Tech Stack Lengkap

### Frontend / UI
| Library | Versi | Fungsi |
|---|---|---|
| Streamlit | 1.43.2 | Framework web app Python |
| Plotly | 5.24.1 | Visualisasi interaktif (radar, bar) |

### AI / ML
| Library | Versi | Fungsi |
|---|---|---|
| groq | 0.13.1 | Client Groq API (LLM + Vision) |
| sentence-transformers | 3.3.1 | Embedding lokal (all-MiniLM-L6-v2) |

**Model yang digunakan:**
- `llama-3.3-70b-versatile` — parsing CV & generasi penjelasan
- `meta-llama/llama-4-scout-17b-16e-instruct` — Vision OCR untuk PDF gambar

### PDF Processing
| Library | Versi | Fungsi |
|---|---|---|
| pdfplumber | 0.11.4 | Ekstraksi teks dengan layout |
| pymupdf | 1.24.14 | Fallback ekstraksi + render gambar |
| pillow | 11.3.0 | Pemrosesan gambar |
| pytesseract | 0.3.13 | OCR lokal (opsional, perlu binary) |

### Database & Backend
| Library | Versi | Fungsi |
|---|---|---|
| supabase | 2.11.0 | Client Supabase/PostgreSQL |
| python-dotenv | 1.0.1 | Manajemen environment variables |

### Data Science
| Library | Versi | Fungsi |
|---|---|---|
| pandas | 2.2.3 | Manipulasi data tabular |
| numpy | 1.26.4 | Operasi matriks (AHP, TOPSIS) |
| scipy | 1.13.1 | Komputasi ilmiah |

### Utilities
| Library | Versi | Fungsi |
|---|---|---|
| pydantic | 2.9.2 | Validasi schema data |
| tenacity | 9.0.0 | Retry logic untuk API calls |
| loguru | 0.7.3 | Structured logging |
| openpyxl | 3.1.5 | Export Excel |

---

## 12. Konfigurasi

### Environment Variables (`.env`)

```env
# Wajib
GROQ_API_KEY=gsk_...
SUPABASE_URL=https://xxxx.supabase.co      # tanpa /rest/v1/
SUPABASE_ANON_KEY=eyJ...

# Opsional (ada default)
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
EMBEDDING_MODEL=all-MiniLM-L6-v2
APP_ENV=production
```

### Streamlit (`.streamlit/config.toml`)

```toml
[server]
port = 8501
address = "localhost"
maxUploadSize = 100        # MB
fileWatcherType = "none"   # Hindari error PyTorch watcher

[theme]
base = "dark"
primaryColor = "#a78bfa"
backgroundColor = "#0f172a"
secondaryBackgroundColor = "#1e293b"
textColor = "#e2e8f0"
```

---

## 13. Cara Pengembangan Lanjutan

### Menambah Template Lowongan

Edit `data/job_templates.py` dan tambahkan entry baru:

```python
"Nama Kategori": {
    "job_family": "Nama Kategori",
    "required_education_level": "S1",
    "required_education_field": "bidang relevan",
    "required_experience_months": 24,
    "required_skills": ["skill1", "skill2"],
    "required_certifications": [],
    "required_languages": ["Indonesia", "English"],
}
```

### Menambah Kriteria Baru

1. Tambah field baru di `app/config.py → AHP_CRITERIA`
2. Implementasi fungsi scoring di `core/dimension_calculator.py`
3. Tambah label di `CRIT_LABELS` pada semua halaman yang relevan
4. Update skema database di `db/migrations/`

### Mengubah Model LLM

Cukup ubah di `.env`:
```env
GROQ_MODEL=llama-3.1-8b-instant   # lebih cepat, lebih murah
```

---

## 14. Troubleshooting

| Error | Penyebab | Solusi |
|---|---|---|
| `PGRST205: table not found` | Migrasi DB belum dijalankan | Jalankan `001_initial_schema.sql` di SQL Editor Supabase |
| `PGRST125: Invalid path` | URL Supabase salah format | Pastikan tidak ada `/rest/v1/` di `SUPABASE_URL` |
| `42501: RLS policy violation` | Row Level Security aktif | Disable RLS untuk semua tabel di Supabase Dashboard |
| OCR gagal / teks kosong | PDF berupa gambar | Sistem auto-fallback ke Groq Vision, pastikan `GROQ_API_KEY` valid |
| `torch.classes RuntimeError` | Inkompatibilitas PyTorch-Streamlit | Sudah diatasi dengan `fileWatcherType = "none"` |
| Penjelasan AI generik | Profil kandidat kosong | Pastikan CV berhasil di-parse (status "success") sebelum analisis |

---

## 15. Tim Pengembang

| NIM | Nama |
|---|---|
| 225150407111061 | Ambar Willis Widiansyah |
| 235150400111033 | Anugerah Gabriel Hutajulu |
| 235150407111038 | Andhika Daniswara Hidayat |
| 235150407111021 | Raditya Ramadhan Firdanto |
| 225150407111030 | Rubens Willsandro Taimenas |

---

*Dokumentasi ini mencerminkan kondisi sistem per Mei 2026.*
