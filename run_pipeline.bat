@echo off
cd /d "%~dp0"
echo ====================================================
echo JALANKAN PIPELINE HARIAN DEATH CROSS: %date% %time%
echo ====================================================

:: Menjalankan impor data dari CSV ke DB secara otomatis
echo [1/3] Menjalankan auto_import.py...
python auto_import.py

:: Menjalankan analisis teknikal (contoh: TLKM)
echo [2/3] Menjalankan run_analysis.py...
python run_analysis.py tlkm

:: Menjalankan prediksi model AI (contoh: TLKM)
echo [3/3] Menjalankan predict_death_cross.py...
python predict_death_cross.py tlkm

echo ====================================================
echo PIPELINE HARIAN SELESAI DIJALANKAN.
echo ====================================================
