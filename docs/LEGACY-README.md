# 🧠 RecruitAI — Sistem Seleksi Kandidat Berbasis AI

**Sistem Pendukung Keputusan (SPK) untuk Seleksi Kandidat Multi-Kriteria**  
Universitas Brawijaya · Fakultas Ilmu Komputer · 2026

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43.2-red)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Database-Supabase-green)](https://supabase.com)
[![Groq](https://img.shields.io/badge/LLM-Groq-orange)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)

---

## 📌 Deskripsi

RecruitAI adalah aplikasi web berbasis AI yang membantu tim HR melakukan seleksi kandidat secara **objektif, transparan, dan efisien**. Sistem ini menggabungkan kecerdasan buatan untuk membaca CV dengan metode pengambilan keputusan multi-kriteria untuk menghasilkan peringkat kandidat yang dapat dipertanggungjawabkan.

### Kemampuan Utama

| Fitur | Keterangan |
|---|---|
| 📄 **Baca CV Otomatis** | Upload PDF → AI ekstrak nama, skill, pengalaman, pendidikan secara otomatis |
| 🖼️ **Dukung PDF Gambar** | CV berupa scan/gambar diproses via Groq Vision API (tanpa instalasi tambahan) |
| ⚖️ **Atur Prioritas Kriteria** | Interface intuitif untuk menentukan bobot tiap kriteria menggunakan metode AHP |
| 🚀 **Analisis Satu Klik** | Jalankan 3 algoritma perbandingan sekaligus, hasilkan peringkat otomatis |
| 📊 **Dashboard HR-Friendly** | Hasil disajikan dalam bahasa yang mudah dipahami tanpa istilah teknis |
| 🤖 **Penjelasan AI** | Setiap kandidat mendapat penilaian naratif dalam Bahasa Indonesia |
| 💾 **Ekspor Excel/CSV** | Unduh hasil seleksi lengkap untuk dokumentasi |

---

## 🚀 Cara Menjalankan

### Prasyarat
- Python 3.11+
- Akun [Supabase](https://supabase.com) (gratis)
- API Key [Groq](https://console.groq.com) (gratis)

### 1. Clone & Konfigurasi

```bash
git clone <repo-url>
cd resume-auto-selection
```

### 2. Setup Environment Variables

Buat file `.env` (salin dari `.env.example`):

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
GROQ_API_KEY=gsk_...
```

> **Penting:** `SUPABASE_URL` hanya berupa base URL saja (tanpa `/rest/v1/`)

### 3. Setup Database Supabase

1. Buka [supabase.com](https://supabase.com) → buat project baru
2. Masuk ke **SQL Editor** → klik **New query**
3. Copy seluruh isi file `db/migrations/001_initial_schema.sql`
4. Paste dan klik **Run**

### 4. Jalankan Lokal

```bash
# Buat virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# atau: source venv/bin/activate  (Mac/Linux)

# Install dependencies
pip install -r requirements.txt

# Jalankan aplikasi
streamlit run app/main.py
# Buka: http://localhost:8501
```

### 5. Jalankan dengan Docker

```bash
docker compose up --build
# Aplikasi tersedia di: http://localhost:8501
```

---

## 📖 Panduan Penggunaan

Ikuti langkah-langkah berikut secara berurutan:

| Langkah | Menu | Keterangan |
|---|---|---|
| 1 | 💼 **Kelola Lowongan** | Buat lowongan, pilih template, isi persyaratan |
| 2 | 📄 **Upload CV** | Upload PDF kandidat (bisa banyak sekaligus) |
| 3 | ⚖️ **Atur Prioritas** | Tentukan bobot kriteria lewat perbandingan berpasangan |
| 4 | 🚀 **Jalankan Analisis** | Satu klik untuk analisis semua kandidat |
| 5 | 📊 **Lihat Hasil** | Baca peringkat, penilaian AI, dan unduh laporan |

---

## 🗂️ Struktur Proyek

```
resume-auto-selection/
├── app/
│   ├── main.py                   # Halaman utama (Home)
│   ├── config.py                 # Konfigurasi global
│   └── pages/
│       ├── 01_job_vacancies.py   # Kelola lowongan (create + edit + delete)
│       ├── 02_upload_resumes.py  # Upload CV & parsing AI
│       ├── 03_ahp_wizard.py      # Wizard prioritas kriteria (AHP)
│       ├── 04_run_analysis.py    # Jalankan analisis multi-kriteria
│       └── 05_results.py         # Dashboard hasil seleksi
├── core/
│   ├── resume_parser.py          # PDF → JSON terstruktur (3-strategy extraction)
│   ├── semantic_scorer.py        # Semantic skill matching (sentence-transformers)
│   ├── dimension_calculator.py   # Kalkulasi 5 dimensi skor [0,1]
│   ├── llm_explainer.py          # Penjelasan AI berbahasa Indonesia
│   └── mcdm/
│       ├── ahp.py                # AHP: pairwise comparison + CR validation
│       ├── saw.py                # SAW: Simple Additive Weighting
│       ├── weighted_product.py   # WP: Weighted Product
│       ├── topsis.py             # TOPSIS: distance to ideal solution
│       └── ensemble.py           # Borda Count aggregation
├── db/
│   ├── supabase_client.py        # Koneksi Supabase
│   ├── repositories.py           # CRUD layer (vacancies, candidates, results)
│   └── migrations/
│       └── 001_initial_schema.sql  # Skema database lengkap
├── data/
│   └── job_templates.py          # 10+ template kategori pekerjaan
├── .streamlit/
│   └── config.toml               # Konfigurasi tema & server Streamlit
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## ⚙️ Cara Kerja Sistem

### Pipeline Parsing CV

```
PDF File
  │
  ├─► [Strategy 1] pdfplumber  → word-based layout extraction
  │
  ├─► [Strategy 2] PyMuPDF     → fallback untuk layout kompleks
  │
  └─► [Strategy 3] Groq Vision → OCR untuk PDF scan/gambar
          │
          ▼
      Raw Text → Groq LLM (llama-3.3-70b) → Structured JSON
          │
          ▼
      CandidateProfile (name, email, education, experience, skills, ...)
```

### Pipeline Analisis

```
CandidateProfile + JobVacancy
        │
        ▼
  Dimension Calculator
  ┌──────────────────────────────┐
  │ • Pendidikan  (level + field)│
  │ • Pengalaman  (qty + relevan)│
  │ • Keahlian    (semantic sim) │
  │ • Sertifikasi (semantic sim) │
  │ • Bahasa      (fulfillment)  │
  └──────────────────────────────┘
        │
  Decision Matrix [0,1]
        │
        ├─► SAW    → score + rank
        ├─► WP     → score + rank
        └─► TOPSIS → score + rank
                │
                ▼
          Borda Count Ensemble
                │
                ▼
         Final Ranking + AI Explanation (Bahasa Indonesia)
```

---

## 🧮 Detail Algoritma

### AHP (Analytic Hierarchy Process)
- Perbandingan berpasangan antar 5 kriteria menggunakan skala Saaty 1–9
- Validasi Consistency Ratio (CR < 0.10 wajib dipenuhi)
- Output: vektor bobot w₁...w₅ yang dijumlah = 1

### Ensemble MCDM

| Algoritma | Formula | Karakteristik |
|---|---|---|
| **SAW** | Σ(wᵢ · rᵢⱼ) | Linier, mudah diinterpretasi |
| **WP** | Π(xᵢⱼ^wᵢ) | Multiplikatif, sensitif terhadap nilai rendah |
| **TOPSIS** | d⁻/(d⁺+d⁻) | Berbasis jarak ke solusi ideal |
| **Borda Count** | Σrank | Agregasi rank dari 3 algoritma di atas |

### Semantic Scoring
Skill matching menggunakan **cosine similarity** dari embeddings `all-MiniLM-L6-v2`:
```
score = cosine_similarity(embed(candidate_skills), embed(required_skills))
```

---

## 🛠️ Tech Stack

| Komponen | Teknologi | Versi |
|---|---|---|
| **UI Framework** | Streamlit | 1.43.2 |
| **LLM Inference** | Groq API (llama-3.3-70b + llama-4-scout Vision) | - |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | 3.3.1 |
| **PDF Extraction** | pdfplumber + PyMuPDF | 0.11.4 / 1.24.14 |
| **Database** | Supabase (PostgreSQL) | 2.11.0 |
| **Visualisasi** | Plotly | 5.24.1 |
| **Export** | openpyxl (Excel) | 3.1.5 |
| **Container** | Docker + Docker Compose | - |

---

## 🔧 Konfigurasi Lanjutan

### `.streamlit/config.toml`
```toml
[server]
port = 8501
address = "localhost"
maxUploadSize = 100       # Max ukuran upload per file (MB)
fileWatcherType = "none"  # Nonaktifkan watcher (kompatibilitas PyTorch)

[theme]
base = "dark"
primaryColor = "#a78bfa"
backgroundColor = "#0f172a"
```

### Groq Models yang Digunakan
- **Text parsing & explanation**: `llama-3.3-70b-versatile`
- **Vision OCR (PDF gambar)**: `meta-llama/llama-4-scout-17b-16e-instruct`

---

## 👥 Tim Pengembang

| NIM | Nama |
|---|---|
| 225150407111061 | Ambar Willis Widiansyah |
| 235150400111033 | Anugerah Gabriel Hutajulu |
| 235150407111038 | Andhika Daniswara Hidayat |
| 235150407111021 | Raditya Ramadhan Firdanto |
| 225150407111030 | Rubens Willsandro Taimenas |

---

## 📝 Catatan

- **PDF scan/gambar**: Diproses via Groq Vision (maks. 4 halaman per file)
- **Minimal kandidat**: Butuh ≥ 2 CV dengan status "berhasil dibaca" untuk analisis
- **AHP Consistency**: CR harus < 0.10, sistem memvalidasi otomatis
- **Bahasa output AI**: Semua penjelasan dan ringkasan dalam Bahasa Indonesia
