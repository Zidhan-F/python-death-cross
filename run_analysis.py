import os
import sys
import json
import shutil
import webbrowser
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
import plotly.graph_objects as go
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

def main():
    print("=" * 60)
    print("       DEATH CROSS Technical Analysis Pipeline")
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

    # 2. Get target stock from user
    default_stock = 'tlkm'
    target_input = input(f"Masukkan kode saham yang ingin dianalisis (default: {default_stock}): ").strip()
    target_stock = target_input.lower() if target_input else default_stock.lower()

    print(f"\nMenghubungkan ke database '{db_name}'...")
    db_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db_name}"
    engine = create_engine(db_url)

    query = f"""
        SELECT tanggal as "Date", close_price as "Close", volume as "Volume", open_price as "Open", high_price as "High", low_price as "Low"
        FROM {table_name}
        WHERE kode = :stock_code
        ORDER BY tanggal ASC
    """

    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn, params={"stock_code": target_stock})

        if df.empty:
            print(f"\nERROR: Tidak ada data untuk kode saham '{target_stock.upper()}' di database.")
            sys.exit(1)

        df['Date'] = pd.to_datetime(df['Date'])
        print(f"SUCCESS: Berhasil memuat {len(df)} baris data untuk saham '{target_stock.upper()}'")

    except Exception as e:
        print(f"\nERROR: Gagal memuat data dari database: {e}")
        sys.exit(1)

    # 3. Calculate Technical Indicators (SMA 5 & SMA 20)
    SHORT_WINDOW = 5
    LONG_WINDOW = 20

    df['SMA_5'] = df['Close'].rolling(window=SHORT_WINDOW).mean()
    df['SMA_20'] = df['Close'].rolling(window=LONG_WINDOW).mean()

    # Detect crossover points (Death Cross)
    df['Position'] = np.where(df['SMA_5'] > df['SMA_20'], 1, 0)
    df['Crossover'] = df['Position'].diff()
    df['Death_Cross'] = np.where(df['Crossover'] == -1, True, False)
    df['Signal'] = np.where(df['Death_Cross'], 'DEATH CROSS', 'HOLD')
    df.loc[(df['Signal'] == 'HOLD') & (df['Position'] == 1), 'Signal'] = 'SAFE'

    death_cross_events = df[df['Death_Cross'] == True]
    print(f"Sinyal Death Cross terdeteksi: {len(death_cross_events)}")
    if len(death_cross_events) > 0:
        print(death_cross_events[['Date', 'Close', 'SMA_5', 'SMA_20', 'Signal']])

    # 4. Generate Static Premium Chart (Matplotlib)
    print("\nMembuat grafik statis...")
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6.5))
    fig.patch.set_facecolor('#12121c')
    ax.set_facecolor('#12121c')

    ax.plot(df['Date'], df['Close'], label='Harga Penutupan (Close)', color='#4e9af1', linewidth=1.5, alpha=0.7)
    ax.plot(df['Date'], df['SMA_5'], label='SMA 5', color='#f39c12', linewidth=1.8)
    ax.plot(df['Date'], df['SMA_20'], label='SMA 20', color='#e74c3c', linewidth=2.0)

    if len(death_cross_events) > 0:
        ax.scatter(death_cross_events['Date'], death_cross_events['Close'], 
                   color='#e74c3c', marker='v', s=150, zorder=5, label='DEATH CROSS SIGNAL', edgecolors='white')
        for _, row in death_cross_events.iterrows():
            ax.annotate(f"Death Cross\n{row['Date'].strftime('%Y-%m-%d')}", 
                        (row['Date'], row['Close']), textcoords="offset points", 
                        xytext=(0,15), ha='center', fontsize=9, color='#e74c3c', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#12121c', edgecolor='#e74c3c', alpha=0.8),
                        arrowprops=dict(arrowstyle="->", color='#e74c3c', lw=1.5))

    ax.set_title(f"Analisis Sinyal Death Cross Saham {target_stock.upper()}", fontsize=14, color='white', fontweight='bold', pad=15)
    ax.set_xlabel('Tanggal', fontsize=12, color='white')
    ax.set_ylabel('Harga (IDR)', fontsize=12, color='white')
    ax.grid(True, linestyle='--', color='#2c2c35', alpha=0.5)
    ax.legend(loc='best', facecolor='#12121c', edgecolor='#2c2c35', labelcolor='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#2c2c35')

    chart_filename = f"death_cross_{target_stock}.png"
    plt.savefig(chart_filename, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"Grafik statis disimpan: {chart_filename}")

    # 5. Generate Interactive Chart (Plotly)
    print("\nMembuat grafik interaktif...")
    fig_interactive = go.Figure()

    fig_interactive.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Close'], 
        name='Close Price', 
        line=dict(color='#4e9af1', width=2)
    ))

    fig_interactive.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['SMA_5'], 
        name='SMA 5', 
        line=dict(color='#f39c12', width=1.5, dash='dash')
    ))

    fig_interactive.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['SMA_20'], 
        name='SMA 20', 
        line=dict(color='#e74c3c', width=2.0, dash='dash')
    ))

    if not death_cross_events.empty:
        fig_interactive.add_trace(go.Scatter(
            x=death_cross_events['Date'],
            y=death_cross_events['Close'],
            mode='markers+text',
            name='Death Cross Signal',
            text=['Death Cross'] * len(death_cross_events),
            textposition='top center',
            marker=dict(symbol='triangle-down', size=14, color='#e74c3c', line=dict(color='white', width=1)),
            textfont=dict(color='#e74c3c', size=11, family='Outfit, Inter, sans-serif')
        ))

    fig_interactive.update_layout(
        title=dict(
            text=f'Death Cross Technical Analysis (Interactive) - {target_stock.upper()}',
            font=dict(color='white', size=22, family='Outfit, Inter, sans-serif'),
            x=0.5
        ),
        hovermode='x unified',
        paper_bgcolor='#12121c',
        plot_bgcolor='#12121c',
        legend=dict(
            font=dict(color='white'),
            bgcolor='rgba(0,0,0,0)',
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        xaxis=dict(
            title=dict(text='Date', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor='#2c2c35',
            linecolor='#2c2c35',
            rangeslider=dict(visible=False),
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikedash='dash',
            spikecolor='#888888'
        ),
        yaxis=dict(
            title=dict(text='Price (IDR)', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor='#2c2c35',
            linecolor='#2c2c35',
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikedash='dash',
            spikecolor='#888888'
        ),
        margin=dict(l=40, r=40, t=80, b=40)
    )

    html_filename = f'death_cross_{target_stock}_interactive.html'
    fig_interactive.write_html(html_filename)
    print(f"File interaktif disimpan: {html_filename}")

    generic_filename = 'death_cross_interactive.html'
    shutil.copyfile(html_filename, generic_filename)
    print(f"Salinan generik disimpan: {generic_filename}")

    # 6. Auto-open in Web Browser
    print("\nMembuka grafik interaktif di web browser default...")
    webbrowser.open(os.path.abspath(html_filename))
    print("SUCCESS: Analisis selesai!")
    print("=" * 60)

if __name__ == "__main__":
    main()
