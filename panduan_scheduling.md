# Panduan Konfigurasi Penjadwalan Otomatis (Scheduling) Harian

Dokumen ini menjelaskan rancangan arsitektur dan langkah-langkah implementasi untuk menjalankan seluruh pipeline data dan prediksi AI secara otomatis setiap harinya. Dokumen ini disiapkan secara sistematis agar dapat dilampirkan langsung ke dalam laporan tugas akhir/dosen Anda.

---

## 1. Kunci Utama Penjadwalan Otomatis (Bypass Input)

Sebelum sebuah sistem dapat dijalankan secara otomatis (tanpa pengawasan manusia/headless), **skrip program tidak boleh meminta input teks interaktif (`input()`)**. Jika program memanggil `input()`, program akan menggantung (*hang*) selamanya di latar belakang karena tidak ada pengguna yang mengetikkan jawaban.

**Solusi yang telah diterapkan:**
Kami telah memodifikasi berkas [run_analysis.py](file:///C:/Users/Zidhan/Downloads/Python%20Death%20Cross/run_analysis.py) dan [predict_death_cross.py](file:///C:/Users/Zidhan/Downloads/Python%20Death%20Cross/predict_death_cross.py) agar mendukung pembacaan argumen dari Command Line (`sys.argv`). 
*   **Mode Interaktif:** Jika dijalankan biasa (`python run_analysis.py`), program tetap bertanya: *"Masukkan kode saham..."*
*   **Mode Otomatis:** Jika dijalankan dengan argumen (`python run_analysis.py tlkm`), program secara otomatis menganalisis saham `TLKM` tanpa meminta input manual dari keyboard.

---

## 2. Metode A: Penjadwalan Menggunakan Windows Task Scheduler (Tingkat Sistem Operasi)

Metode ini menggunakan aplikasi bawaan Windows OS yang sangat stabil, hemat memori, dan tidak memerlukan skrip Python untuk terus berjalan di latar belakang sepanjang waktu.

Kami telah membuat berkas [run_pipeline.bat](file:///C:/Users/Zidhan/Downloads/Python%20Death%20Cross/run_pipeline.bat) di folder proyek Anda. Batch file ini bertugas mengeksekusi tiga proses berturut-turut:
1.  Mengimpor data terbaru (`auto_import.py`).
2.  Mendeteksi Death Cross teknikal (`run_analysis.py tlkm`).
3.  Melatih model AI & memprediksi risiko esok hari (`predict_death_cross.py tlkm`).

### Langkah Konfigurasi Windows Task Scheduler:
1.  Klik tombol **Start Windows**, ketik **Task Scheduler**, lalu tekan **Enter**.
2.  Pada panel kanan, klik **Create Basic Task...**
3.  **Name & Description:** Isi nama tugas (misalnya: `Death_Cross_Daily_Pipeline`) dan deskripsinya, klik **Next**.
4.  **Trigger:** Pilih **Daily** (Harian), klik **Next**.
5.  **Time:** Tentukan jam eksekusi otomatis. Disarankan pukul **17:00** (Jam 5 sore WIB), karena bursa saham Indonesia (IHSG) telah resmi ditutup pada pukul 16:00, sehingga data transaksi hari tersebut sudah final. Klik **Next**.
6.  **Action:** Pilih **Start a program**, klik **Next**.
7.  **Program/script:** Klik **Browse** dan pilih lokasi berkas [run_pipeline.bat](file:///C:/Users/Zidhan/Downloads/Python%20Death%20Cross/run_pipeline.bat) Anda.
8.  **Start in (optional):** **PENTING!** Masukkan alamat folder proyek Anda (contoh: `C:\Users\Zidhan\Downloads\Python Death Cross`). Jika kolom ini kosong, skrip Python tidak akan menemukan file CSV-nya.
9.  Klik **Next**, lalu klik **Finish**.

Sistem Windows akan secara otomatis membuka CMD di latar belakang setiap jam 5 sore untuk memperbarui database, melakukan perhitungan Moving Average, dan melatih ulang model prediksi AI Anda.

---

## 3. Metode B: Penjadwalan Menggunakan Python Daemon (Tingkat Aplikasi)

Metode ini menggunakan sebuah skrip Python mandiri yang berjalan terus-menerus di latar belakang (*daemon process*) dan memantau waktu secara berkala.

Kami telah membuat berkas [scheduler_harian.py](file:///C:/Users/Zidhan/Downloads/Python%20Death%20Cross/scheduler_harian.py) di folder proyek Anda.

### Cara Menjalankan:
Buka Terminal/CMD di folder proyek Anda, lalu jalankan:
```bash
python scheduler_harian.py
```

### Mekanisme Kerja Kode:
Skrip ini menggunakan pustaka Python `schedule`. Di dalamnya, tugas diatur dengan sintaks yang sangat mudah dibaca:
```python
# Menjadwalkan fungsi run_pipeline setiap hari pada pukul 17:00
schedule.every().day.at("17:00").do(run_pipeline)
```
Program akan melakukan *looping* tanpa batas (`while True`) dengan jeda tidur 1 detik (`time.sleep(1)`) untuk memeriksa apakah waktu saat ini telah menyentuh pukul 17:00. Jika iya, seluruh fungsi pipeline akan dijalankan otomatis.

---

## 4. Teori & Argumentasi untuk Dosen / Laporan Akademik

Saat ditanya oleh dosen mengenai pentingnya dan cara kerja penjadwalan ini, Anda dapat menjelaskan argumentasi teknis berikut:

1.  **Pentingnya Otomatisasi Siklus Data (*Data Lifecycle*):**
    Analisis pasar modal membutuhkan data yang segar (*freshness of data*). Karena perdagangan saham terus bergerak setiap hari kerja, data transaksi harian baru wajib dimasukkan ke database relasional (PostgreSQL) setelah bursa ditutup untuk memperbarui pemahaman model terhadap dinamika pasar terbaru.
2.  **Mekanisme *Retraining* AI (Model Drift Mitigation):**
    Model prediksi risiko (Random Forest) tidak bersifat statis. Model perlu dilatih ulang (*retrained*) secara terjadwal dengan menambahkan data transaksi hari terakhir untuk mencegah degradasi performa model (*model drift*) seiring berjalannya waktu.
3.  **Arsitektur Sistem Terjadwal:**
    Dengan memadukan penjadwal tingkat OS (Windows Task Scheduler) dan kode program tanpa kepala (*headless code*), sistem ini memiliki arsitektur modular yang dapat dengan mudah dipindahkan ke server awan (Cloud Server seperti AWS EC2 atau Google Cloud VM) menggunakan sistem penjadwal Unix standar (**Cron Job**).
