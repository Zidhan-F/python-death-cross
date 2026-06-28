# Panduan Penggunaan: Pipeline Analisis & Pemodelan Death Cross Saham

Panduan ini menjelaskan langkah-langkah praktis untuk menyiapkan lingkungan kerja (*setup environment*), menjalankan pipeline penyerapan data, serta mengeksekusi modul analisis teknikal dan kecerdasan buatan (AI) pada komputer Anda.

---

## 1. Prasyarat Sistem (Prerequisites)

Sebelum menjalankan program, pastikan komputer Anda telah terinstal:
1.  **Python (Versi 3.8 atau yang lebih baru)**.
2.  **PostgreSQL Database Server** yang sedang berjalan secara lokal (*localhost*) atau remote.
3.  File dataset **`transaksi_harian_202606130928.csv`** harus berada di dalam folder yang sama dengan skrip Python.

---

## 2. Langkah-Langkah Penggunaan

### Langkah 1: Setup Konfigurasi Database
Buka berkas [db_config.json](file:///C:/Users/Zidhan/Downloads/Python%20Death%20Cross/db_config.json) menggunakan text editor pilihan Anda, kemudian sesuaikan kata sandi (*password*) dan kredensial PostgreSQL Anda:

```json
{
  "host": "localhost",
  "port": 5432,
  "username": "postgres",
  "password": "MASUKKAN_PASSWORD_POSTGRES_ANDA_DISINI",
  "database": "saham_db",
  "table_name": "transaksi_harian"
}
```

---

### Langkah 2: Impor Data CSV ke PostgreSQL
Untuk memindahkan seluruh baris data dari berkas CSV ke PostgreSQL, Anda dapat menjalankan salah satu dari dua skrip import berikut melalui Terminal atau Command Prompt (CMD).

#### Pilihan A: Impor Otomatis (Direkomendasikan)
Skrip ini akan otomatis memeriksa pustaka Python yang kurang, mendeteksi kata sandi *default*, membuat database secara otomatis jika belum ada, dan melakukan impor data.

Jalankan perintah berikut:
```bash
python auto_import.py
```

#### Pilihan B: Impor Interaktif
Skrip ini akan menanyakan detail koneksi database Anda satu per satu sebelum melakukan proses impor.

Jalankan perintah berikut:
```bash
python import_to_postgres.py
```

**Penjelasan Output Langkah 2:**
*   Skrip akan membaca data CSV dengan pemisah titik koma (`;`).
*   Tabel PostgreSQL bernama `transaksi_harian` akan dibuat/ditimpa dengan skema tipe data SQL yang optimal.
*   Data diunggah dalam potongan kecil (per 5.000 baris) agar menghemat RAM komputer.
*   Di akhir proses, program akan melakukan verifikasi dengan menampilkan jumlah baris data yang sukses diimpor dan menampilkan contoh 5 baris data teratas dari database.

---

### Langkah 3: Jalankan Analisis Teknikal Tradisional (Moving Average)
Untuk mendeteksi titik persilangan *bearish* (Death Cross) historis serta memvisualisasikannya dalam bentuk grafik statis dan interaktif, jalankan perintah berikut:

```bash
python run_analysis.py
```

**Penjelasan Prosedur:**
1.  Program akan meminta masukan kode saham yang ingin dianalisis, contoh: `tlkm` atau `bolt`. Jika Anda langsung menekan **Enter**, program akan menggunakan default saham `tlkm`.
2.  Program akan menarik data harga historis saham dari PostgreSQL, lalu menghitung indikator `SMA 5` dan `SMA 20`.
3.  Program mendeteksi persilangan di mana garis `SMA 5` memotong ke bawah garis `SMA 20` (Sinyal Death Cross).
4.  **Output Visualisasi yang Terbentuk:**
    *   **Grafik Statis (`death_cross_<kode_saham>.png`):** Gambar grafik bertema gelap dengan penanda segitiga merah di setiap titik kejadian Death Cross.
    *   **Grafik Interaktif (`death_cross_<kode_saham>_interactive.html`):** Halaman web HTML interaktif yang akan **otomatis terbuka di browser default** Anda. Anda bisa mengarahkan kursor (*hover*) untuk melihat detail harga harian dan menggeser/memperbesar grafik.

---

### Langkah 4: Jalankan Model AI untuk Prediksi Risiko Real-Time
Untuk melatih kecerdasan buatan (*Random Forest Classifier*) guna memprediksi potensi kemunculan sinyal Death Cross dalam 5 hari ke depan, jalankan perintah berikut:

```bash
python predict_death_cross.py
```

**Penjelasan Prosedur:**
1.  Masukkan kode saham yang ingin diprediksi (contoh: `tlkm`).
2.  Program akan memproses data saham tersebut dan melakukan *Feature Engineering* (membuat 7 fitur masukan untuk AI) serta melakukan pelabelan target (*Labeling Target*).
3.  Program membagi data menjadi 80% Data Latih (*Train*) dan 20% Data Uji (*Test*).
4.  Model Random Forest dilatih, kemudian menampilkan metrik evaluasi seperti Akurasi dan Laporan Klasifikasi (*Precision, Recall, F1-Score*).
5.  Program akan menyimpan grafik pentingnya fitur dengan nama `ai_feature_importance.png`.
6.  **Prediksi Real-time Hari Berikutnya:**
    Program membaca baris data transaksi hari terakhir, lalu mengeluarkan probabilitas terjadinya Death Cross dalam 5 hari ke depan beserta status risikonya:
    *   **SAFE** (Aman/Stabil): Probabilitas di bawah 40%.
    *   **WARNING** (Waspada Tren Bearish): Probabilitas antara 40% - 69%.
    *   **CRITICAL** (Bahaya Penurunan Tajam): Probabilitas mencapai 70% atau lebih.

---

### Langkah Opsional: Menjalankan Eksperimen di Jupyter Notebook
Bila Anda ingin melakukan modifikasi parameter atau eksplorasi data secara visual langkah demi langkah:
1.  Pastikan Anda berada di direktori proyek di terminal.
2.  Jalankan perintah:
    ```bash
    jupyter notebook
    ```
3.  Buka berkas [postgres_death_cross.ipynb](file:///C:/Users/Zidhan/Downloads/Python%20Death%20Cross/postgres_death_cross.ipynb) melalui browser atau text editor VS Code.
4.  Jalankan setiap sel kode (*code cell*) berurutan dari atas ke bawah untuk melihat proses kalkulasi indikator dan plot grafik interaktif.
