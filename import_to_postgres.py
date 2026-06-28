# -*- coding: utf-8 -*-
"""
Script to Import Stock CSV Data to PostgreSQL
Created for: transaksi_harian_202606130928.csv
"""

import os
import sys
import subprocess
import getpass

# 1. Pastikan library pendukung terpasang
def install_requirements():
    print("Checking database driver dependencies...")
    required_libs = ["pandas", "sqlalchemy", "psycopg2-binary"]
    installed = []
    
    for lib in required_libs:
        try:
            __import__(lib.replace("-binary", ""))
            installed.append(lib)
        except ImportError:
            print(f"Installing missing library: {lib}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--quiet"])
                print(f"Successfully installed {lib}.")
                installed.append(lib)
            except Exception as e:
                print(f"Failed to install {lib}: {e}")
                print("Please install it manually using: pip install " + lib)
                sys.exit(1)
    print("All dependencies are ready!\n")

install_requirements()

import pandas as pd
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, text
# pyrefly: ignore [missing-import]
from sqlalchemy.types import Date, String, Float, BigInteger, Integer

def get_connection_details():
    print("=" * 60)
    print("    POSTGRESQL CONNECTION CONFIGURATION")
    print("=" * 60)
    
    host = input("PostgreSQL Host [default: localhost]: ").strip() or "localhost"
    port = input("PostgreSQL Port [default: 5432]: ").strip() or "5432"
    user = input("PostgreSQL Username [default: postgres]: ").strip() or "postgres"
    password = getpass.getpass("PostgreSQL Password [default: postgres]: ").strip() or "postgres"
    db_name = input("Database Name [default: saham_db]: ").strip() or "saham_db"
    table_name = input("Table Name [default: transaksi_harian]: ").strip() or "transaksi_harian"
    
    return host, port, user, password, db_name, table_name

def create_database_if_not_exists(host, port, user, password, db_name):
    # Connect to default 'postgres' database first to check/create the target database
    temp_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    temp_engine = create_engine(temp_url, isolation_level="AUTOCOMMIT")
    
    try:
        with temp_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = :db_name"), {"db_name": db_name})
            exists = result.scalar()
            
            if not exists:
                print(f"Database '{db_name}' not found. Creating it now...")
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Database '{db_name}' already exists. Connecting to it...")
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to PostgreSQL or create database: {e}")
        print("Please check if your PostgreSQL service is running and credentials are correct.")
        sys.exit(1)
    finally:
        temp_engine.dispose()

def import_csv_to_postgres():
    csv_path = "transaksi_harian_202606130928.csv"
    if not os.path.exists(csv_path):
        # Try parent folder or search for csv in active directory
        print(f"Searching for CSV in current folder...")
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'transaksi_harian' in f]
        if csv_files:
            csv_path = csv_files[0]
            print(f"Found CSV file: {csv_path}")
        else:
            print("[ERROR] CSV file 'transaksi_harian_202606130928.csv' not found in this folder.")
            sys.exit(1)
            
    print(f"Reading CSV file '{csv_path}'...")
    try:
        # CSV uses semicolon (;) delimiter based on header inspection
        df = pd.read_csv(csv_path, sep=';')
        print(f"Loaded CSV successfully. Total Rows: {len(df):,}, Total Columns: {len(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        sys.exit(1)

    # Get DB details from user
    host, port, user, password, db_name, table_name = get_connection_details()
    
    # Create DB if missing
    create_database_if_not_exists(host, port, user, password, db_name)
    
    # Reconnect to target database
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_engine(db_url)
    
    # Clean data types
    print("\nPreparing data structure...")
    
    # Parse date column
    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal']).dt.date
    
    # Map pandas types to SQLAlchemy types for precise table definition
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
    
    # Check if df has all these columns and align names
    actual_dtypes = {col: dtype_mapping[col] for col in df.columns if col in dtype_mapping}
    
    print(f"Importing data into table '{table_name}' in database '{db_name}'...")
    try:
        # Use pandas to_sql for automatic schema creation and insert
        # if exists 'replace' will recreate table with correct columns
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='replace',
            index=False,
            dtype=actual_dtypes,
            chunksize=5000
        )
        print(f"SUCCESS! Imported {len(df):,} rows into table '{table_name}'.")
    except Exception as e:
        print(f"\n[ERROR] Failed to write data to PostgreSQL: {e}")
        sys.exit(1)
        
    # Verify import by reading back some rows
    print("\n" + "="*50)
    print("    VERIFYING DATA IN POSTGRESQL TABLE")
    print("="*50)
    try:
        with engine.connect() as conn:
            # Get table count
            count_res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            total_rows = count_res.scalar()
            print(f"Total Rows in DB table '{table_name}': {total_rows:,}")
            
            # Show first 5 rows
            print(f"\nFirst 5 rows from database:")
            sample_df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
            print(sample_df.to_string(index=False))
            
            # Show basic statistics
            print(f"\nTop 5 Stock Codes by Total Volume:")
            stats_query = f"""
                SELECT kode, SUM(volume) as total_volume, ROUND(AVG(close_price)::numeric, 2) as avg_close_price
                FROM {table_name}
                GROUP BY kode
                ORDER BY total_volume DESC
                LIMIT 5
            """
            stats_df = pd.read_sql_query(stats_query, conn)
            print(stats_df.to_string(index=False))
            
    except Exception as e:
        print(f"[WARNING] Failed to run verification query: {e}")
    finally:
        engine.dispose()
        
    print("\n" + "="*50)
    print("Process Completed successfully.")
    print("="*50)

if __name__ == "__main__":
    try:
        import_csv_to_postgres()
    except KeyboardInterrupt:
        print("\nProcess cancelled by user.")
        sys.exit(0)
