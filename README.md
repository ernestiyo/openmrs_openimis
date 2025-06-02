# OpenMRS-OpenIMIS Integration Middleware untuk Klinik Desa

Sistem integrasi untuk menghubungkan OpenMRS (sistem rekam medis) dengan OpenIMIS (sistem klaim asuransi kesehatan) menggunakan standar FHIR. Sistem ini dibangun menggunakan FastAPI untuk backend dan Streamlit untuk antarmuka pengguna. Didesain khusus untuk konteks klinik desa di Indonesia.

## Fitur Utama

- 🧑‍⚕️ **Pendaftaran Pasien**: 
  - Pendaftaran pasien baru dengan informasi dasar
  - Sistem keluhan utama dengan dropdown dan opsi kustom
  - Antarmuka dalam Bahasa Indonesia

- 📝 **Kunjungan Medis**: 
  - Pencatatan kunjungan, diagnosis, dan pengobatan
  - Daftar obat dengan harga dalam Rupiah
  - Perhitungan otomatis total biaya pengobatan

- 💰 **Klaim Asuransi**: 
  - Generate dan ajukan klaim FHIR
  - Proses persetujuan/penolakan klaim
  - Tampilan status klaim (diajukan/disetujui/ditolak)

- 📊 **Pelaporan**: 
  - Statistik bulanan dengan rincian biaya dalam Rupiah
  - Laporan pasien, kunjungan, dan klaim
  - Filter dan analisis data terperinci

- ⚙️ **Administrasi**: 
  - Manajemen sistem dan statistik
  - Reset data dengan konfirmasi
  - Antarmuka pengguna yang mudah digunakan

## Prasyarat

- Python 3.8 atau lebih tinggi
- pip (Penginstal paket Python)

## Instalasi

1. Clone repositori ini:
```powershell
git clone https://github.com/ernestiyo/openmrs_openimis.git
cd openmrs_openimis
```

2. Buat dan aktifkan virtual environment (opsional tapi direkomendasikan):
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

3. Install dependensi yang diperlukan:
```powershell
pip install -r requirements.txt
```

## Menjalankan Aplikasi

Aplikasi ini terdiri dari dua komponen yang harus dijalankan secara terpisah:

1. Jalankan server backend FastAPI:
```powershell
uvicorn main:app --reload
```
Backend akan tersedia di http://localhost:8000

2. Di terminal baru, jalankan frontend Streamlit:
```powershell
streamlit run app.py
```
Frontend akan otomatis terbuka di browser default Anda di http://localhost:8501

## Usage

1. **Pendaftaran Pasien**
   - Pilih "Pendaftaran Pasien" di sidebar
   - Isi data pasien (nama, usia, jenis kelamin)
   - Pilih keluhan utama dari daftar atau tambahkan keluhan kustom
   - Simpan data pasien baru

2. **Pencatatan Kunjungan**
   - Buka "Catat Kunjungan"
   - Pilih pasien dari daftar
   - Masukkan diagnosis dan pilih obat dari daftar
   - Lihat perhitungan total biaya otomatis dalam Rupiah
   - Tambahkan catatan pengobatan jika diperlukan
   - Simpan kunjungan

3. **Pengelolaan Klaim**
   - Akses "Ajukan & Proses Klaim"
   - Untuk mengajukan klaim:
     - Pilih kunjungan dari daftar
     - Review detail klaim FHIR
     - Ajukan klaim
   - Untuk memproses klaim:
     - Lihat daftar klaim yang menunggu
     - Review detail klaim
     - Setujui atau tolak klaim

4. **Laporan Bulanan**
   - Buka "Laporan Bulanan"
   - Pilih bulan untuk melihat statistik
   - Lihat rincian:
     - Total biaya obat dalam Rupiah
     - Status klaim asuransi
     - Filter data berdasarkan diagnosis
   - Review tabel detail pasien, kunjungan, dan klaim

5. **Administrasi**
   - Akses statistik sistem
   - Lihat total pasien, kunjungan, dan klaim
   - Reset data jika diperlukan (memerlukan konfirmasi)

## Dokumentasi API

Backend FastAPI menyediakan dokumentasi API otomatis:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Struktur Proyek

```
openmrs_openimis/
├── main.py           # Server backend FastAPI
├── app.py           # Aplikasi frontend Streamlit
└── requirements.txt  # Daftar dependensi Python
```

## Detail Teknis

- Backend: FastAPI dengan penyimpanan in-memory
- Frontend: Streamlit dengan komponen interaktif
- Format Data: JSON yang sesuai dengan standar FHIR
- Bahasa: Antarmuka dalam Bahasa Indonesia
- Mata Uang: Rupiah (IDR)
- Fitur Khusus:
  - Daftar obat dengan harga standar
  - Sistem keluhan dengan opsi preset
  - Perhitungan otomatis biaya dalam Rupiah
  - Manajemen persetujuan klaim

## Keterbatasan

- Menggunakan penyimpanan in-memory (data hilang saat server restart)
- Kepatuhan FHIR dasar untuk demonstrasi
- Belum terhubung ke sistem OpenMRS atau OpenIMIS yang sebenarnya
- Fitur keamanan terbatas
- Belum ada fitur pencetakan resep atau kwitansi
- Belum ada manajemen stok obat

## Pengembangan

Untuk memodifikasi atau mengembangkan aplikasi:

1. Perubahan Backend:
   - Edit `main.py` untuk menambah/mengubah endpoint API
   - Gunakan model Pydantic untuk validasi data
   - Restart server uvicorn untuk menerapkan perubahan

2. Perubahan Frontend:
   - Modifikasi `app.py` untuk mengupdate UI
   - Perubahan akan otomatis dimuat ulang oleh Streamlit

## Pemecahan Masalah

1. Jika tidak bisa terhubung ke backend:
   - Pastikan server FastAPI sedang berjalan
   - Periksa apakah port 8000 tersedia

2. Jika frontend tidak mau dimuat:
   - Verifikasi instalasi Streamlit
   - Periksa apakah port 8501 bebas
   - Bersihkan cache browser jika perlu

3. Jika data tidak tersimpan:
   - Ingat bahwa ini adalah sistem in-memory
   - Data akan hilang saat server di-restart
