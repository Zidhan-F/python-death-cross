# Laporan Teknis: Arsitektur Data, Pipeline, dan Pemodelan Prediksi Sinyal Death Cross Saham

Laporan ini disusun untuk menjelaskan struktur proyek, alur pemrosesan data (data pipeline), detail fungsional dari file-file kode program, serta metodologi pemodelan AI yang digunakan untuk mendeteksi dan memprediksi sinyal pergerakan tren *bearish* (**Death Cross**) pada instrumen saham.

---

## 1. Struktur Proyek dan Deskripsi Berkas

Berikut adalah tata letak direktori proyek analisis data dan pemodelan AI:

```text
📁 Python Death Cross/
│
├── 📁 .venv/                               # Virtual environment Python (berisi dependensi lokal)
├── 📁 __pycache__/                         # Cache file bytecode Python compiled
│
├── 📄 db_config.json                       # Berkas konfigurasi koneksi ke database PostgreSQL
├── 📄 requirements.txt                     # Daftar pustaka (dependencies) Python yang dibutuhkan
│
├── 📄 transaksi_harian_202606130928.csv   # Dataset mentah transaksi harian bursa saham (CSV)
│
├── 🐍 auto_import.py                       # Skrip impor otomatis data CSV ke PostgreSQL (dengan fallback)
├── 🐍 import_to_postgres.py                # Skrip interaktif impor data CSV ke PostgreSQL
├── 🐍 run_analysis.py                      # Skrip analisis teknikal Moving Average tradisional & grafik (Plotly/Matplotlib)
├── 🐍 predict_death_cross.py               # Skrip pemodelan predictive AI dengan Random Forest Classifier
│
├── 📓 postgres_death_cross.ipynb           # Jupyter Notebook untuk eksplorasi interaktif & pengembangan model
│
├── 🖼️ ai_feature_importance.png           # Grafik visualisasi kontribusi fitur pada keputusan model AI
├── 🖼️ death_cross_tlkm.png                 # Grafik statis analisis teknikal (Matplotlib) untuk saham TLKM
├── 🌐 death_cross_tlkm_interactive.html    # Grafik interaktif berbasis web (Plotly) untuk saham TLKM
└── 🌐 death_cross_interactive.html         # Salinan generik grafik interaktif untuk hasil analisis terakhir
```

### Penjelasan Fungsional Tiap Berkas:
*   **`db_config.json`**: Menyimpan data kredensial akses PostgreSQL agar skrip Python dapat terhubung secara dinamis dan aman tanpa melakukan *hardcoding* pada berkas skrip utama.
*   **`requirements.txt`**: Mendefinisikan pustaka Python beserta versinya untuk memastikan replikasi lingkungan kerja (*environment reproducibility*) berjalan dengan lancar.
*   **`transaksi_harian_202606130928.csv`**: File data transaksi bursa saham Indonesia yang berisi kolom penting seperti tanggal, kode saham, harga pembukaan, penutupan, volume, frekuensi, dan nilai transaksi.
*   **`import_to_postgres.py` / `auto_import.py`**: Bertanggung jawab memindahkan data dari file CSV ke tabel relasional database PostgreSQL secara terstruktur untuk menjamin keandalan data (data integrity) dan performa query yang cepat.
*   **`run_analysis.py`**: Melakukan kalkulasi indikator teknikal (SMA 5 & SMA 20) dan mendeteksi persilangan garis tren turun (*crossover* Death Cross) secara retrospektif (sesudah kejadian).
*   **`predict_death_cross.py`**: Mengimplementasikan model kecerdasan buatan (*supervised machine learning*) untuk memprediksi probabilitas terjadinya Death Cross sebelum sinyal tersebut benar-benar terbentuk di pasar (fungsi *early warning*).
*   **`postgres_death_cross.ipynb`**: Lingkungan eksperimen terisolasi bagi analis data untuk menulis kode baris demi baris, melihat hasil secara instan, dan melakukan eksplorasi data.

---

## 2. Diagram Alur Data (Data Pipeline)

Sistem ini dirancang menggunakan alur pipa data (*data pipeline*) yang terintegrasi, dimulai dari penyerapan data mentah (*data ingestion*), penyimpanan terstruktur, pengolahan fitur (*feature engineering*), pelatihan model AI, hingga tahap visualisasi keluaran.

```mermaid
graph TD
    A["Data Mentah: transaksi_harian_...csv"] -->|1. Pandas read_csv| B("Penyerap Data: auto_import.py / import_to_postgres.py")
    B -->|2. SQLAlchemy ORM Mapping & Type Cast| C[("Database PostgreSQL: saham_db")]
    C -->|3. Query Deret Waktu Terfilter (SQL)"| D("Pipeline Analisis: run_analysis.py / predict_death_cross.py")
    D -->|4. Feature Engineering| E["Ekstraksi Fitur Teknis (Volume Ratio, Volatility, SMA)"]
    E -->|5. Labeling Temporal| F["Membentuk Variabel Target y (Death Cross dalam 5 Hari)"]
    F -->|6. Pembagian Data| G["Random Forest Classifier (Supervised AI Model)"]
    G -->|7. Model Evaluasi & Inferensi| H["Visualisasi (Interactive Plotly HTML, Static PNG & Prediksi Real-time)"]
```

---

## 3. Penjelasan Kode Sumber (Source Code & Penjelasannya)

Bagian ini memaparkan kode-kode program utama di dalam proyek beserta analisis baris program secara mendalam.

### A. Konfigurasi Lingkungan Kerja & Database

#### 1. File `requirements.txt`
Berkas ini berisi dependensi pustaka luar (third-party libraries) yang harus diinstal untuk menjalankan pipeline ini.
```text
pandas>=2.0.0
numpy>=1.20.0
matplotlib>=3.5.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
plotly>=5.0.0
scikit-learn>=1.0.0
```
*   **`pandas`** & **`numpy`**: Pengolahan dataset, manipulasi baris dan kolom, operasi matematika vektor.
*   **`sqlalchemy`** & **`psycopg2-binary`**: Penghubung (*Object-Relational Mapping* / ORM) antara Python dan database PostgreSQL.
*   **`matplotlib`** & **`plotly`**: Pembuatan visualisasi data dalam bentuk grafik statis (.png) maupun interaktif berbasis web (.html).
*   **`scikit-learn`**: Menyediakan kerangka kerja Machine Learning (pemisahan dataset, algoritma Random Forest, laporan evaluasi performa model).

#### 2. File `db_config.json`
Konfigurasi koneksi yang bersifat dinamis.
```json
{
  "host": "localhost",
  "port": 5432,
  "username": "postgres",
  "password": "YOUR_PASSWORD_HERE",
  "database": "saham_db",
  "table_name": "transaksi_harian"
}
```

---

### B. Ingesti Data ke PostgreSQL

Program penyerap data mendeteksi berkas CSV, melakukan pembersihan data (*data cleaning*), melakukan pemetaan jenis kolom (*schema mapping*), dan memasukannya ke database PostgreSQL.

#### File `auto_import.py`
Berikut adalah cuplikan kode krusial dari mekanisme impor otomatis:
```python
# Menentukan pemetaan tipe data Pandas ke tipe data SQL presisi
dtype_mapping = {
    'tanggal': Date,
    'kode': String(20),
    'prev_price': Float,
    'open_price': Float,
    'close_price': Float,
    'high_price': Float,
    'low_price': Float,
    'volume': BigInteger,
    'frekuensi': Integer,
    'offer': Float,
    'offer_volume': BigInteger,
    'bid': Float,
    'bid_volume': BigInteger,
    'changes_pct': Float,
    'high_changes_pct': Float,
    'low_changes_pct': Float,
    'range_intraday_pct': Float,
    'gap_up_pct': Float,
    'nilai_transaksi_mil': Float
}

actual_dtypes = {col: dtype_mapping[col] for col in df.columns if col in dtype_mapping}

# Eksekusi migrasi data ke database
df.to_sql(
    name=table_name,
    con=engine,
    if_exists='replace', # Hapus tabel lama dan buat baru jika sudah ada
    index=False,
    dtype=actual_dtypes,
    chunksize=5000       # Mengirim data per 5.000 baris agar tidak membebani memori server
)
```

**Penjelasan Alur `auto_import.py`:**
1.  **Instalasi Dependensi Otomatis:** Memeriksa apakah pustaka pendukung terpasang, jika tidak ada, ia memanggil sub-proses `pip install` tanpa campur tangan pengguna.
2.  **Pemuatan Konfigurasi:** Membaca berkas `db_config.json`.
3.  **Kredensial Pintar:** Jika kata sandi masih bernilai default, sistem mencoba kata sandi umum seperti `"postgres"`, `""`, `"admin"`, `"123456"`, dll. Jika gagal, ia akan meminta masukan manual dari pengguna.
4.  **Pembuatan Database Otomatis:** Menghubungkan ke PostgreSQL lokal, memeriksa apakah database `saham_db` ada, jika belum, perintah `CREATE DATABASE` dikirimkan secara langsung.
5.  **Schema Enforcement:** Konversi kolom `tanggal` menjadi objek tanggal standar SQL, memetakan tipe data data-frame pandas ke struktur SQL, lalu mengimpornya dengan skema optimal menggunakan parameter `chunksize` untuk meminimalkan beban memori.

---

### C. Pipeline Analisis Teknikal Tradisional

#### File `run_analysis.py`
Program ini menghitung Simple Moving Average (SMA) harian dan mendeteksi titik persilangan tren *bearish*.

```python
# 1. Menghitung Indikator Teknikal SMA 5 dan SMA 20
SHORT_WINDOW = 5
LONG_WINDOW = 20

df['SMA_5'] = df['Close'].rolling(window=SHORT_WINDOW).mean()
df['SMA_20'] = df['Close'].rolling(window=LONG_WINDOW).mean()

# 2. Logika Deteksi Crossover Death Cross
df['Position'] = np.where(df['SMA_5'] > df['SMA_20'], 1, 0)
df['Crossover'] = df['Position'].diff()
df['Death_Cross'] = np.where(df['Crossover'] == -1, True, False)

# 3. Labeling Sinyal untuk Visualisasi
df['Signal'] = np.where(df['Death_Cross'], 'DEATH CROSS', 'HOLD')
df.loc[(df['Signal'] == 'HOLD') & (df['Position'] == 1), 'Signal'] = 'SAFE'
```

**Penjelasan Alur Kerja `run_analysis.py`:**
1.  **Pemuatan Data Terarah:** Mengambil riwayat transaksi untuk kode saham tertentu (misal: `TLKM`) yang diurutkan menaik berdasarkan kolom `tanggal` dari database PostgreSQL.
2.  **Kalkulasi Moving Average:**
    *   **SMA 5 (Jangka Pendek):** Rata-rata pergerakan harga penutupan selama 5 hari terakhir.
    *   **SMA 20 (Jangka Panjang):** Rata-rata pergerakan harga penutupan selama 20 hari terakhir.
3.  **Logika Penentuan Crossover:**
    *   `Position`: Jika SMA 5 > SMA 20 maka bernilai `1` (kondisi *bullish* atau stabil), selain itu bernilai `0`.
    *   `Crossover`: Hasil selisih harga baris ke-$t$ dengan baris ke-$(t-1)$ dari kolom `Position`. Jika nilainya berubah dari `1` ke `0`, maka selisihnya (`diff()`) akan bernilai `-1`.
    *   `Death_Cross`: Nilai `-1` menandakan persilangan garis tren turun (**SMA 5 memotong ke bawah SMA 20**), yang menandai datangnya fase penurunan harga signifikan (*bearish*).
4.  **Ekspansi Visualisasi:**
    *   **Matplotlib:** Membuat visualisasi grafik statis bertema gelap, menandai setiap kejadian Death Cross dengan segitiga terbalik berwarna merah lengkap dengan anotasi tanggal kejadiannya, lalu menyimpannya ke format file `.png`.
    *   **Plotly:** Menghasilkan grafik lilin/garis interaktif yang responsif di web browser, memfasilitasi pembacaan data koordinat hover yang detail, dan menyimpannya sebagai berkas `.html`.

---

### D. Pipeline Pemodelan Predictive AI

#### File `predict_death_cross.py`
Skrip ini bertujuan memprediksi risiko terjadinya Death Cross dalam 5 hari perdagangan berikutnya menggunakan kecerdasan buatan.

```python
# 1. FEATURE ENGINEERING (Variabel Input / X)
df['SMA_5'] = df['Close'].rolling(window=5).mean()
df['SMA_20'] = df['Close'].rolling(window=20).mean()
df['SMA_50'] = df['Close'].rolling(window=50).mean()

# Jarak persentase antara SMA 5 dan SMA 20
df['Pct_Diff_SMA5_SMA20'] = (df['SMA_5'] - df['SMA_20']) / df['SMA_20']
# Rasio harga penutupan terhadap rata-rata pergerakan trennya
df['Price_to_SMA5'] = df['Close'] / df['SMA_5']
df['Price_to_SMA20'] = df['Close'] / df['SMA_20']

# Logika Pengembalian & Risiko Volatilitas Harga
df['Daily_Return'] = df['Close'].pct_change()
df['Volatility_5d'] = df['Daily_Return'].rolling(window=5).std()
df['Volatility_20d'] = df['Daily_Return'].rolling(window=20).std()

# Rasio volume hari ini dengan volume rata-rata 5 hari terakhir
df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=5).mean()

# 2. TARGET LABELING (Variabel y)
df['Position'] = np.where(df['SMA_5'] > df['SMA_20'], 1, 0)
df['Death_Cross_Today'] = np.where(df['Position'].diff() == -1, 1, 0)

# Shift ke masa depan (-5) dan gunakan Rolling Window max 5 hari
df['Target'] = df['Death_Cross_Today'].shift(-5).rolling(window=5, min_periods=1).max()
df['Target'] = df['Target'].fillna(0).astype(int)
```

**Penjelasan Feature Engineering & Target Model AI:**
*   **Kenapa AI?** Pendekatan tradisional hanya memberitahukan kejadian Death Cross *setelah* itu terjadi (indikator lagging). Model AI bertindak sebagai *Early Warning System* untuk memprediksi risiko tersebut *sebelum* terbentuk.
*   **7 Variabel Prediktor (X):**
    1.  `Pct_Diff_SMA5_SMA20`: Kedekatan jarak relatif kedua garis rata-rata pergerakan. Semakin mendekati nol atau bernilai negatif kecil, semakin rawan terjadi perpotongan tren.
    2.  `Price_to_SMA5` & `Price_to_SMA20`: Posisi harga penutupan terakhir relatif terhadap rata-rata pergerakan harian.
    3.  `Daily_Return`: Mengukur persentante fluktuasi laba/rugi harian saham.
    4.  `Volatility_5d` & `Volatility_20d`: Mengukur penyimpangan/ketidakstabilan pergerakan harga dalam rentang jangka pendek (5 hari) dan jangka menengah (20 hari).
    5.  `Volume_Ratio`: Rasio volume guna mendeteksi partisipasi pasar yang tidak wajar (lonjakan atau penurunan volume drastis).
*   **Penetapan Target Prediksi (y):**
    Target model didefinisikan sebagai klasifikasi biner:
    *   `1 (Berisiko)`: Jika Death Cross akan terjadi di masa depan dalam jendela rentang 1 hingga 5 hari ke depan ($t+1$ s/d $t+5$).
    *   `0 (Aman)`: Tidak ada potensi kejadian Death Cross dalam 5 hari ke depan.
    Mekanisme pergeseran logis data temporal diimplementasikan menggunakan:
    `df['Death_Cross_Today'].shift(-5).rolling(window=5, min_periods=1).max()`

```python
# 3. PROSES PELATIHAN MODEL
# Pembagian data: 80% untuk melatih model, 20% untuk pengujian
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Inisialisasi model klasifikasi Random Forest
rf_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, class_weight='balanced')
rf_model.fit(X_train, y_train)
```

**Konfigurasi Pembelajaran Machine Learning:**
*   `train_test_split(..., stratify=y)`: Memastikan distribusi sampel target (`1` dan `0`) seimbang dan representatif pada data latih (*train*) maupun data uji (*test*).
*   `n_estimators=100`: Membangun 100 pohon keputusan independen untuk agregasi voting prediksi guna memperkecil varians model.
*   `max_depth=5`: Membatasi kedalaman maksimal pohon untuk menghindari model mengingat data latihan secara berlebihan (*overfitting*).
*   `class_weight='balanced'`: Parameter kritis untuk mengatasi data yang tidak seimbang (*imbalanced dataset*), di mana jumlah hari "Stabil (y=0)" jauh lebih banyak dibanding hari "Bahaya (y=1)". Bobot kelas otomatis disesuaikan secara berbanding terbalik dengan frekuensi kemunculan kelas tersebut.

---

## 4. Evaluasi Model dan Hasil Analisis AI

### A. Metrik Performa Model AI (Dataset Saham TLKM)
Berdasarkan hasil pelatihan dengan menggunakan data historis TLKM, performa yang dihasilkan adalah sebagai berikut:

*   **Model Accuracy:** **89.74%**
*   **Hasil Laporan Klasifikasi (Classification Report):**
    *   **Kelas 0 (No Risk / Stabil):**
        *   *Precision:* 97% (Ketika model memprediksi kondisi aman, keakuratannya mencapai 97%).
        *   *Recall:* 90% (Sistem mampu menyaring 90% dari keseluruhan hari yang tergolong aman di dunia nyata).
    *   **Kelas 1 (Death Cross Risk / Risiko Bearish):**
        *   *Precision:* 70% (Saat model mendeteksi adanya risiko sinyal turun dalam 5 hari ke depan, 70% dari peringatan tersebut terbukti benar terjadi).
        *   *Recall:* **88%** (Sensitivitas sistem sangat tinggi, mampu menangkap 88% dari total potensi kejutan pasar Death Cross sebelum terjadi).
        *   *F1-Score:* 78% (Nilai harmonis penyeimbang antara presisi dan daya tangkap sinyal).

### B. Hasil Pentingnya Fitur (Feature Importance)
Model AI secara otomatis mengevaluasi faktor internal data yang paling berkontribusi dalam menentukan peluang persilangan garis tren turun. Pengaruh relatif masing-masing fitur adalah sebagai berikut:

| Peringkat | Nama Fitur / Variabel | Kontribusi Relatif (%) | Deskripsi Fungsional |
| :---: | :--- | :---: | :--- |
| **1** | `Pct_Diff_SMA5_SMA20` | **42.06%** | Jarak relatif antara tren jangka pendek dan panjang. Variabel penentu utama. |
| **2** | `Price_to_SMA20` | **18.70%** | Tingkat ketimpangan harga penutupan saat ini terhadap dasar rata-rata 20 hari. |
| **3** | `Volatility_20d` | **14.49%** | Tingkat ketidakstabilan pergerakan harga historis 20 hari terakhir. |
| **4** | `Price_to_SMA5` | **9.24%** | Tingkat ketimpangan harga terhadap rata-rata pergerakan 5 hari harian. |
| **5** | `Daily_Return` | **5.46%** | Nilai imbal hasil atau performa pergerakan harga hari ini dibanding kemarin. |
| **6** | `Volatility_5d` | **5.27%** | Ketidakstabilan harga harian jangka pendek 5 hari terakhir. |
| **7** | `Volume_Ratio` | **4.78%** | Indeks kekuatan transaksi pasar melalui rasio volume perdagangan. |

---

## 5. Visualisasi Hasil Model

Sistem menghasilkan berkas visualisasi keluaran utama untuk interpretasi hasil bagi pengambil keputusan:

### 1. Grafik Kontribusi Fitur (`ai_feature_importance.png`)
Grafik ini dihasilkan oleh `predict_death_cross.py` dan disimpan dalam format gambar statis bertema gelap premium. Grafik ini menunjukkan dengan jelas bobot keputusan model Random Forest.

### 2. Grafik Interaktif HTML (`death_cross_tlkm_interactive.html` / `death_cross_interactive.html`)
Berkas HTML interaktif ini dapat dibuka di web browser modern secara langsung. Fitur utama grafik ini meliputi:
*   Grafik garis interaktif harga penutupan historis beserta garis indikator tren `SMA 5` dan `SMA 20`.
*   Penanda segitiga merah ke bawah (`triangle-down`) bertuliskan **"Death Cross"** di setiap titik koordinat hari di mana persilangan garis tren bearish terdeteksi.
*   Fitur interaksi *Zoom-in*, *Zoom-out*, *Pan*, serta *Unified Hover Tooltip* yang menampilkan nilai harga penutupan dan nilai Moving Average secara serentak ketika kursor melintasi area grafik.
