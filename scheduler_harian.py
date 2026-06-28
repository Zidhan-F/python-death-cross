import os
import sys
import time
import subprocess
from datetime import datetime

# Pastikan library 'schedule' terpasang
try:
    import schedule
except ImportError:
    print("Installing 'schedule' library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "schedule", "--quiet"])
    import schedule

def run_pipeline():
    print("\n" + "="*60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MEMULAI PIPELINE JADWAL HARIAN...")
    print("="*60)
    
    # 1. Jalankan auto_import.py
    print("[1/3] Menjalankan auto_import.py...")
    subprocess.run([sys.executable, "auto_import.py"])
    
    # 2. Jalankan run_analysis.py untuk TLKM
    print("\n[2/3] Menjalankan run_analysis.py tlkm...")
    subprocess.run([sys.executable, "run_analysis.py", "tlkm"])
    
    # 3. Jalankan predict_death_cross.py untuk TLKM
    print("\n[3/3] Menjalankan predict_death_cross.py tlkm...")
    subprocess.run([sys.executable, "predict_death_cross.py", "tlkm"])
    
    print("\n" + "="*60)
    print("PIPELINE HARIAN BERHASIL DISELESAIKAN!")
    print("="*60)

# Jadwalkan setiap hari pada jam 17:00 (waktu setelah penutupan bursa saham IHSG)
TARGET_TIME = "17:00"
schedule.every().day.at(TARGET_TIME).do(run_pipeline)

print("="*60)
print(f"  SCHEDULER PIPELINE DEATH CROSS AKTIF")
print(f"  Pipeline akan dijalankan otomatis setiap hari jam: {TARGET_TIME}")
print("  Tekan Ctrl+C untuk menghentikan scheduler.")
print("="*60)

# Jalankan pipeline sekali di awal untuk memastikan semuanya berfungsi
run_pipeline()

try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("\nScheduler dihentikan oleh pengguna.")
