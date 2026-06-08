# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import getpass
import json

def install_dependencies():
    print("Checking database library dependencies...")
    for lib in ["pandas", "sqlalchemy", "psycopg2-binary"]:
        try:
            __import__(lib.replace("-binary", ""))
        except ImportError:
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--quiet"])

install_dependencies()

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import Date, String, Float, BigInteger, Integer

CONFIG_FILE = "db_config.json"

def load_config():
    default_config = {
        "host": "localhost",
        "port": 5432,
        "username": "postgres",
        "password": "zidhan24",
        "database": "saham_db",
        "table_name": "transaksi_harian"
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=2)
        return default_config
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[WARNING] Failed to save config file: {e}")

def try_connections(host, port, user):
    passwords = ["postgres", "", "admin", "root", "123456", "1234"]
    print("\nAttempting default connection credentials to local PostgreSQL...")
    for pwd in passwords:
        db_url = f"postgresql://{user}:{pwd}@{host}:{port}/postgres"
        try:
            engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[SUCCESS] Connected successfully using password: '{pwd}'")
            return pwd
        except Exception:
            continue
    print("[WARNING] Could not connect using default passwords.")
    return None

def verify_connection(host, port, user, pwd):
    db_url = f"postgresql://{user}:{pwd}@{host}:{port}/postgres"
    try:
        engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

def main():
    csv_file = "transaksi_harian_202605251952.csv"
    if not os.path.exists(csv_file):
        print(f"[ERROR] CSV file {csv_file} not found in this folder.")
        return
        
    print(f"[INFO] Reading CSV file: {csv_file}...")
    try:
        df = pd.read_csv(csv_file, sep=";")
        print(f"[INFO] CSV data loaded successfully: {len(df):,} rows.")
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        return
    
    # Convert tanggal column to date format
    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal']).dt.date

    config = load_config()
    host = config.get("host", "localhost")
    port = config.get("port", 5432)
    user = config.get("username", "postgres")
    pwd = config.get("password", "YOUR_PASSWORD_HERE")
    db_name = config.get("database", "saham_db")
    table_name = config.get("table_name", "transaksi_harian")

    # If password is still placeholder, try defaults, then prompt
    if pwd == "YOUR_PASSWORD_HERE":
        pwd = try_connections(host, port, user)
        if pwd is None:
            print("\nPlease enter your PostgreSQL password manually:")
            pwd = getpass.getpass("Password: ")
            # Verify manually typed password
            if not verify_connection(host, port, user, pwd):
                print("[ERROR] Connection failed with the provided password.")
                return
        config["password"] = pwd
        save_config(config)
    else:
        # Verify the saved password
        if not verify_connection(host, port, user, pwd):
            print(f"[WARNING] Saved password in '{CONFIG_FILE}' failed to connect. Retrying with defaults...")
            pwd = try_connections(host, port, user)
            if pwd is None:
                print("\nPlease enter your PostgreSQL password manually:")
                pwd = getpass.getpass("Password: ")
                if not verify_connection(host, port, user, pwd):
                    print("[ERROR] Connection failed with the provided password.")
                    return
            config["password"] = pwd
            save_config(config)

    # Create database if it doesn't exist
    temp_url = f"postgresql://{user}:{pwd}@{host}:{port}/postgres"
    try:
        temp_engine = create_engine(temp_url, isolation_level="AUTOCOMMIT")
        with temp_engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :db_name"), {"db_name": db_name})
            if not result.scalar():
                print(f"[INFO] Database '{db_name}' not found. Creating database...")
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"[SUCCESS] Database '{db_name}' created successfully.")
            else:
                print(f"[INFO] Database '{db_name}' already exists.")
        temp_engine.dispose()
    except Exception as e:
        print(f"[ERROR] Failed to check/create database: {e}")
        return

    # Connect to target database
    target_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db_name}"
    engine = create_engine(target_url)
    
    # Define column type mapping
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
    
    print(f"[INFO] Importing data to table '{table_name}'...")
    try:
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='replace',
            index=False,
            dtype=actual_dtypes,
            chunksize=5000
        )
        print(f"[SUCCESS] Imported {len(df):,} rows into table '{table_name}' in database '{db_name}'.")
        
        # Verify the import
        with engine.connect() as conn:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            print(f"[INFO] Verified row count in database: {cnt:,}")
            
            print("\n[INFO] Preview of the first 5 rows in PostgreSQL:")
            sample = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
            print(sample.to_string(index=False))
            
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
