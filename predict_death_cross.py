import os
import sys
import json
# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

def main():
    print("=" * 60)
    print("      AI / Machine Learning Death Cross Prediction Model")
    print("=" * 60)

    # 1. Load database configuration
    config_path = 'db_config.json'
    if not os.path.exists(config_path):
        print(f"ERROR: File '{config_path}' tidak ditemukan.")
        print("Silakan jalankan 'auto_import.py' terlebih dahulu untuk setup database.")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = json.load(f)

    user = config.get('username', 'postgres')
    pwd = config.get('password', 'postgres')
    host = config.get('host', 'localhost')
    port = config.get('port', 5432)
    db_name = config.get('database', 'saham_db')
    table_name = config.get('table_name', 'transaksi_harian')

    # Get target stock from user or command line arguments
    default_stock = 'tlkm'
    if len(sys.argv) > 1:
        target_stock = sys.argv[1].lower()
        print(f"Menggunakan kode saham dari argumen command-line: {target_stock.upper()}")
    else:
        target_input = input(f"Masukkan kode saham untuk pemodelan AI (default: {default_stock}): ").strip()
        target_stock = target_input.lower() if target_input else default_stock.lower()

    print(f"\nMenghubungkan ke database '{db_name}'...")
    db_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db_name}"
    engine = create_engine(db_url)

    query = f"""
        SELECT tanggal as "Date", close_price as "Close", volume as "Volume", 
               open_price as "Open", high_price as "High", low_price as "Low"
        FROM {table_name}
        WHERE kode = :stock_code
        ORDER BY tanggal ASC
    """

    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn, params={"stock_code": target_stock})

        if len(df) < 50:
            print(f"\nERROR: Data saham '{target_stock.upper()}' terlalu sedikit (minimal 50 baris untuk training).")
            sys.exit(1)

        df['Date'] = pd.to_datetime(df['Date'])
        print(f"SUCCESS: Berhasil memuat {len(df)} baris data untuk modeling AI.")

    except Exception as e:
        print(f"\nERROR: Gagal memuat data dari database: {e}")
        sys.exit(1)

    # 2. FEATURE ENGINEERING (Mempersiapkan Variabel Prediktor / X)
    print("\n[AI Modeling] Mengekstrak fitur-fitur teknikal...")
    
    # Simple Moving Averages
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # Momentum & Tren
    df['Diff_SMA5_SMA20'] = df['SMA_5'] - df['SMA_20']
    df['Pct_Diff_SMA5_SMA20'] = (df['SMA_5'] - df['SMA_20']) / df['SMA_20']
    df['Price_to_SMA5'] = df['Close'] / df['SMA_5']
    df['Price_to_SMA20'] = df['Close'] / df['SMA_20']
    
    # Return & Volatilitas Harian
    df['Daily_Return'] = df['Close'].pct_change()
    df['Volatility_5d'] = df['Daily_Return'].rolling(window=5).std()
    df['Volatility_20d'] = df['Daily_Return'].rolling(window=20).std()
    
    # Volume Change
    df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=5).mean()

    # 3. TARGET DEFINITION (Mempersiapkan Label Prediksi / y)
    # Target: Apakah Death Cross (SMA_5 memotong ke bawah SMA_20) terjadi dalam 5 hari ke depan?
    df['Position'] = np.where(df['SMA_5'] > df['SMA_20'], 1, 0)
    df['Crossover'] = df['Position'].diff()
    df['Death_Cross_Today'] = np.where(df['Crossover'] == -1, 1, 0)
    
    # Cari tahu apakah ada Death Cross di masa depan (shifiting backwards)
    # y = 1 jika dalam 5 baris ke depan (hari ke t+1 s/d t+5) terdapat Death_Cross_Today == 1
    df['Target'] = df['Death_Cross_Today'].shift(-5).rolling(window=5, min_periods=1).max()
    df['Target'] = df['Target'].fillna(0).astype(int)

    # Hapus baris kosong (NaN) akibat rolling window
    df_model = df.dropna().copy()
    
    if len(df_model) < 20:
        print("ERROR: Terlalu banyak data kosong untuk melatih model AI.")
        sys.exit(1)

    # Fitur yang digunakan untuk pelatihan AI
    features = [
        'Pct_Diff_SMA5_SMA20', 
        'Price_to_SMA5', 
        'Price_to_SMA20', 
        'Daily_Return', 
        'Volatility_5d', 
        'Volatility_20d', 
        'Volume_Ratio'
    ]

    X = df_model[features]
    y = df_model['Target']

    print(f"Jumlah sampel training: {len(df_model)} baris.")
    print(f"Distribusi Target (1: Akan Death Cross, 0: Stabil/Tidak):")
    print(y.value_counts())

    # 4. TRAINING MACHINE LEARNING MODEL
    print("\n[AI Modeling] Melatih model Random Forest Classifier...")
    # Split data menjadi Train (80%) dan Test (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Inisialisasi model Random Forest
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, class_weight='balanced')
    rf_model.fit(X_train, y_train)

    # Evaluasi Model
    y_pred = rf_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n" + "=" * 50)
    # print("              METRIK EVALUASI AI MODEL")
    print(f"Model Accuracy: {accuracy * 100:.2f}%")
    print("-" * 50)
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['No Risk', 'Death Cross Risk']))
    print("=" * 50)

    # 5. FEATURE IMPORTANCE (Analisis Pengaruh Fitur terhadap Keputusan AI)
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[::-1]

    print("\nKontribusi Fitur Terhadap Prediksi AI (Feature Importance):")
    for f_idx in range(len(features)):
        print(f"{f_idx + 1}. {features[indices[f_idx]]}: {importances[indices[f_idx]] * 100:.2f}%")

    # Plot Feature Importance
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#12121c')
    ax.set_facecolor('#12121c')
    
    colors = plt.cm.plasma(np.linspace(0.4, 0.8, len(features)))
    bars = ax.barh([features[i] for i in indices[::-1]], [importances[i] for i in indices[::-1]], color=colors)
    ax.set_title("AI Feature Importance - Variabel Kunci Prediksi Death Cross", fontsize=12, fontweight='bold', color='white', pad=15)
    ax.set_xlabel('Nilai Pengaruh Relatif', fontsize=10, color='white')
    ax.grid(True, linestyle='--', color='#2c2c35', alpha=0.5)
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#2c2c35')

    chart_filename = "ai_feature_importance.png"
    plt.savefig(chart_filename, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"\n[Visualisasi] Grafik Feature Importance disimpan ke: {chart_filename}")

    # 6. RUN REAL-TIME PREDICTION ON LATEST DATA
    latest_data = df.iloc[-1]
    latest_features = pd.DataFrame([{
        'Pct_Diff_SMA5_SMA20': (latest_data['SMA_5'] - latest_data['SMA_20']) / latest_data['SMA_20'] if not pd.isna(latest_data['SMA_20']) else 0.0,
        'Price_to_SMA5': latest_data['Close'] / latest_data['SMA_5'] if not pd.isna(latest_data['SMA_5']) else 1.0,
        'Price_to_SMA20': latest_data['Close'] / latest_data['SMA_20'] if not pd.isna(latest_data['SMA_20']) else 1.0,
        'Daily_Return': df['Close'].pct_change().iloc[-1] if len(df) > 1 else 0.0,
        'Volatility_5d': df['Close'].pct_change().rolling(window=5).std().iloc[-1] if len(df) > 5 else 0.0,
        'Volatility_20d': df['Close'].pct_change().rolling(window=20).std().iloc[-1] if len(df) > 20 else 0.0,
        'Volume_Ratio': latest_data['Volume'] / df['Volume'].rolling(window=5).mean().iloc[-1] if len(df) > 5 else 1.0
    }])

    # Clean any possible NaN in latest features
    latest_features = latest_features.fillna(0.0)

    # Predict probability
    predicted_prob = rf_model.predict_proba(latest_features)[0][1]
    
    print("\n" + "=" * 60)
    print("             PREDIKSI RISIKO DEATH CROSS OLEH AI")
    print("=" * 60)
    print(f"Saham yang dianalisis: {target_stock.upper()}")
    print(f"Tanggal Data Terakhir : {latest_data['Date'].strftime('%Y-%m-%d')}")
    print(f"Harga Penutupan Terakhir: IDR {latest_data['Close']:,.2f}")
    print(f"Probabilitas Kejadian Death Cross dalam 5 Hari Kerja Ke Depan: {predicted_prob * 100:.2f}%")
    
    if predicted_prob >= 0.7:
        print("STATUS RISIKO: [CRITICAL] Tren turun sangat kuat terdeteksi!")
    elif predicted_prob >= 0.4:
        print("STATUS RISIKO: [WARNING] Waspada perpotongan harga ke bawah (Bearish Trend).")
    else:
        print("STATUS RISIKO: [SAFE] Tren aman / stabil.")
    print("=" * 60)

if __name__ == "__main__":
    main()
