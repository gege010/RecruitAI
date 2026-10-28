# RecruitAI Workspace

Ruang seleksi kandidat berbasis web untuk tim HR: lowongan yang dapat dikustomisasi,
ekstraksi CV, pembandingan multi-kriteria, dan keputusan manusia yang dapat ditelusuri.
Aplikasi v2 menggunakan FastAPI dan antarmuka web mandiri, tanpa Streamlit.

## Jalankan di Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Buka http://127.0.0.1:8000. Ruang kerja dimulai kosong. Buat lowongan pertama atau
pilih **Jelajahi data contoh** untuk memuat enam profil fiktif. Data disimpan dalam
`var/recruitai.sqlite3`. Salin `.env.example` ke `.env` hanya jika belum memiliki
konfigurasi; jangan menimpa kredensial yang sudah ada.

## Alur penggunaan

1. Buat lowongan: keahlian, durasi pengalaman, pendidikan, sertifikasi, bahasa.
2. Tambah kandidat melalui PDF atau profil manual. PDF maksimal 10 MB / 20 halaman.
3. Verifikasi profil: nama, keahlian, pendidikan, durasi pengalaman dan bahasa.
4. Atur lima bobot hingga total 100% pada Kriteria seleksi.
5. Jalankan analisis. SAW, WP, TOPSIS digabung dengan Borda; nilai sama tetap seri.
6. Buka bukti kandidat; simpan shortlist, pertimbangkan atau tidak dilanjutkan.
   Keputusan tidak dilanjutkan wajib memiliki catatan.
7. Ekspor CSV dari snapshot analisis. Status dalam CSV adalah status saat analisis.

Skor persen berarti kesesuaian terhadap persyaratan yang diisi, bukan peluang
keberhasilan kerja. Informasi belum diketahui perlu diverifikasi. Mengubah kandidat
atau kriteria menandai hasil lama; jalankan analisis ulang untuk memperbaruinya.

## AI dan pemrosesan lokal

Ekstraksi lokal menggunakan teks PDF dan pencocokan kata kunci eksplisit. Durasi
pengalaman tidak ditebak. PDF scan belum didukung; gunakan PDF teks atau profil
manual. Groq bersifat opsional: atur `GROQ_API_KEY`, lalu pilih bantuan AI pada
unggahan. Hanya pilihan tersebut yang mengirim teks CV ke Groq. Hasil AI tetap
harus diverifikasi. Tidak ada panggilan AI untuk menentukan keputusan HR.

## Deployment

```powershell
# Atur RECRUITAI_PASSWORD (minimal 16 karakter) dan RECRUITAI_ORIGIN pada .env
# Hubungkan reverse proxy HTTPS ke 127.0.0.1:8000
docker compose up --build -d
```

Image berjalan sebagai pengguna non-root, filesystem read-only dan volume data
persisten. Mode production menolak kata sandi lemah. Cookie production hanya dapat
digunakan melalui HTTPS; membuka container langsung melalui HTTP bukan alur login
production yang didukung. Endpoint `/health` memeriksa database. Proxy wajib
membatasi request 12 MB, timeout dan laju permintaan. Gunakan satu worker/replica.

Ini merupakan implementasi satu organisasi dengan satu kata sandi tim. Sebelum
menggunakan data kandidat nyata, lengkapi retensi/penghapusan data, backup terenkripsi,
uji restore, evaluasi kualitas ekstraksi, dan review keamanan dependensi. Belum
mencakup multi-tenant, SSO/RBAC individual, OCR scan, antrean worker terdistribusi,
atau validasi fairness model. Lihat PRODUCT.md dan docs/OPERATIONS.md.

## Verifikasi

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
node --check web/app.js
```

Pengujian browser `tests/browser.cjs` memerlukan Playwright dan Chromium. Jalankan
server pada database uji kosong (`RECRUITAI_DB=var/browser-test.sqlite3`) di port
8001; atur `PLAYWRIGHT_MODULE`, `CHROME_PATH` dan `TEST_URL` sesuai perangkat.
Jangan arahkan pengujian ke ruang kerja dengan data nyata. Screenshot dan laporan
uji ada dalam `artifacts/`.

## Struktur

- `server/`: API, sesi, SQLite, ekstraksi, penilaian, dan snapshot.
- `web/`: antarmuka, komponen bersama, desain responsif dan font lokal berlisensi.
- `core/mcdm/`: AHP, SAW, WP, TOPSIS, Borda dan validasi numerik.
- `tests/`: pengujian perhitungan, API, PDF, desain dan browser.
- `DESIGN.md`, `UX-CONTRACT.md`, `PRODUCT.md`: kontrak desain dan produk.
- `legacy/`: sumber prototipe kuliah (Streamlit/Supabase), tidak dipakai oleh v2.
- `docs/LEGACY-README.md` dan `DOCUMENTATION.md`: referensi proyek awal.

## Repository dan asal proyek

Pengembangan v2 dipisahkan dari repository tugas kuliah. Riwayat Git lama disimpan
lokal di `.git-history/` dan tidak dikirim ke repository baru. `.env`, data kandidat,
venv dan backup riwayat diabaikan Git. Sumber serta atribusi tim awal dipertahankan
di dokumen lama. Tidak ada migrasi otomatis atau perubahan pada database Supabase
lama; v2 memakai penyimpanan sendiri.
