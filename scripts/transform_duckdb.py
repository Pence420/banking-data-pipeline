import os
import duckdb
import pandas as pd
import glob
import json
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "banking.duckdb"
BRONZE_DIR = "data/bronze"
SILVER_DIR = "data/silver"
GOLD_DIR = "data/gold"

os.makedirs(SILVER_DIR, exist_ok=True)
os.makedirs(GOLD_DIR, exist_ok=True)

# Hapus database lama kalo ada
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = duckdb.connect(DB_PATH)

print("🔍 Starting DuckDB Transformations...")
print("=" * 50)

# ============================================================
# BACA DATA DARI BRONZE
# ============================================================
print("\n📂 Reading Bronze layer...")

def read_bronze_files(table_name):
    files = glob.glob(f"{BRONZE_DIR}/{table_name}_*.parquet")
    if not files:
        print(f"⚠️ No files found for {table_name}")
        return None
    
    df_list = []
    for f in files:
        df = pd.read_parquet(f)
        df_list.append(df)
    
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    return None

df_customers_raw = read_bronze_files("customers")
df_accounts_raw = read_bronze_files("accounts")
df_transactions_raw = read_bronze_files("transactions")

if df_customers_raw is not None:
    print(f"✅ Loaded {len(df_customers_raw)} customer records")
    conn.register("bronze_customers", df_customers_raw)
if df_accounts_raw is not None:
    print(f"✅ Loaded {len(df_accounts_raw)} account records")
    conn.register("bronze_accounts", df_accounts_raw)
if df_transactions_raw is not None:
    print(f"✅ Loaded {len(df_transactions_raw)} transaction records")
    conn.register("bronze_transactions", df_transactions_raw)

# ============================================================
# CUSTOMERS
# ============================================================
if df_customers_raw is not None:
    print("\n🧹 Processing customers...")
    
    conn.execute("""
        CREATE OR REPLACE TABLE stg_customers_raw AS
        SELECT 
            operation,
            captured_at,
            data::JSON as data_json
        FROM bronze_customers
    """)
    
    conn.execute("""
        CREATE OR REPLACE TABLE stg_customers AS
        WITH ranked AS (
            SELECT 
                (data_json->>'customer_id')::INT as customer_id,
                data_json->>'full_name' as full_name,
                data_json->>'email' as email,
                data_json->>'address' as address,
                data_json->>'loyalty_tier' as loyalty_tier,
                data_json->>'status' as status,
                data_json->>'created_at' as created_at,
                data_json->>'updated_at' as updated_at,
                captured_at,
                ROW_NUMBER() OVER (
                    PARTITION BY (data_json->>'customer_id')::INT
                    ORDER BY captured_at DESC
                ) as rn
            FROM stg_customers_raw
            WHERE operation IN ('INSERT', 'UPDATE')
        )
        SELECT 
            customer_id,
            full_name,
            email,
            address,
            loyalty_tier,
            status,
            created_at,
            updated_at,
            captured_at as scd_valid_from
        FROM ranked
        WHERE rn = 1
    """)
    
    conn.execute("""
        CREATE OR REPLACE TABLE snap_customers AS
        SELECT 
            customer_id,
            full_name,
            email,
            address,
            loyalty_tier,
            status,
            created_at,
            updated_at,
            scd_valid_from,
            NULL as scd_valid_to,
            TRUE as is_current_record
        FROM stg_customers
    """)
    
    conn.execute("""
        CREATE OR REPLACE TABLE dim_customers AS
        SELECT * FROM snap_customers
    """)
    
    print("✅ Customers done")

# ============================================================
# ACCOUNTS
# ============================================================
if df_accounts_raw is not None:
    print("\n🧹 Processing accounts...")
    
    conn.execute("""
        CREATE OR REPLACE TABLE stg_accounts_raw AS
        SELECT 
            operation,
            captured_at,
            data::JSON as data_json
        FROM bronze_accounts
    """)
    
    conn.execute("""
        CREATE OR REPLACE TABLE stg_accounts AS
        WITH ranked AS (
            SELECT 
                (data_json->>'account_id')::INT as account_id,
                (data_json->>'customer_id')::INT as customer_id,
                data_json->>'account_number' as account_number,
                data_json->>'account_type' as account_type,
                (data_json->>'balance')::DOUBLE as balance,
                data_json->>'status' as status,
                data_json->>'created_at' as created_at,
                captured_at,
                ROW_NUMBER() OVER (
                    PARTITION BY (data_json->>'account_id')::INT
                    ORDER BY captured_at DESC
                ) as rn
            FROM stg_accounts_raw
            WHERE operation IN ('INSERT', 'UPDATE')
        )
        SELECT 
            account_id,
            customer_id,
            account_number,
            account_type,
            balance,
            status,
            created_at,
            captured_at as scd_valid_from
        FROM ranked
        WHERE rn = 1
    """)
    
    conn.execute("""
        CREATE OR REPLACE TABLE snap_accounts AS
        SELECT 
            account_id,
            customer_id,
            account_number,
            account_type,
            balance,
            status,
            created_at,
            scd_valid_from,
            NULL as scd_valid_to,
            TRUE as is_current_record
        FROM stg_accounts
    """)
    
    conn.execute("""
        CREATE OR REPLACE TABLE dim_accounts AS
        SELECT * FROM snap_accounts
        WHERE is_current_record = TRUE
    """)
    
    print("✅ Accounts done")

# ============================================================
# TRANSACTIONS
# ============================================================
if df_transactions_raw is not None:
    print("\n🧹 Processing transactions...")
    
    conn.execute("""
        CREATE OR REPLACE TABLE stg_transactions_raw AS
        SELECT 
            operation,
            captured_at,
            data::JSON as data_json
        FROM bronze_transactions
    """)
    
    conn.execute("""
        CREATE OR REPLACE TABLE stg_transactions AS
        SELECT 
            (data_json->>'transaction_id')::INT as transaction_id,
            (data_json->>'account_id')::INT as account_id,
            data_json->>'transaction_type' as transaction_type,
            (data_json->>'amount')::DOUBLE as amount,
            data_json->>'status' as transaction_status,
            data_json->>'transaction_date' as transaction_date,
            data_json->>'created_at' as created_at,
            captured_at
        FROM stg_transactions_raw
        WHERE operation = 'INSERT'
    """)
    
    conn.execute("""
        CREATE OR REPLACE TABLE fact_transactions AS
        SELECT 
            t.transaction_id,
            t.account_id,
            a.customer_id,
            t.transaction_type,
            t.amount,
            t.transaction_status,
            t.transaction_date,
            t.created_at as transaction_time,
            CASE 
                WHEN t.transaction_status = 'success' THEN t.amount
                ELSE 0 
            END as success_amount
        FROM stg_transactions t
        LEFT JOIN dim_accounts a ON t.account_id = a.account_id
    """)
    
    print("✅ Transactions done")

# ============================================================
# DIM_DATE
# ============================================================
print("\n📅 Creating dim_date...")
conn.execute("""
    CREATE OR REPLACE TABLE dim_date AS
    WITH dates AS (
        SELECT 
            date::DATE as date_key,
            EXTRACT('year' FROM date::DATE) as year,
            EXTRACT('month' FROM date::DATE) as month,
            EXTRACT('day' FROM date::DATE) as day,
            EXTRACT('dow' FROM date::DATE) as day_of_week,
            EXTRACT('quarter' FROM date::DATE) as quarter,
            CASE 
                WHEN EXTRACT('dow' FROM date::DATE) IN (0, 6) THEN TRUE 
                ELSE FALSE 
            END as is_weekend
        FROM generate_series(
            '2024-01-01'::DATE,
            '2026-12-31'::DATE,
            INTERVAL 1 DAY
        ) AS t(date)
    )
    SELECT * FROM dates
""")
print("✅ dim_date created")

# ============================================================
# EXPORT KE PARQUET
# ============================================================
print("\n💾 Exporting to Parquet...")

try:
    conn.execute(f"COPY dim_customers TO '{GOLD_DIR}/dim_customers.parquet' (FORMAT PARQUET)")
    print("✅ dim_customers exported")
except: pass

try:
    conn.execute(f"COPY dim_accounts TO '{GOLD_DIR}/dim_accounts.parquet' (FORMAT PARQUET)")
    print("✅ dim_accounts exported")
except: pass

try:
    conn.execute(f"COPY fact_transactions TO '{GOLD_DIR}/fact_transactions.parquet' (FORMAT PARQUET)")
    print("✅ fact_transactions exported")
except: pass

try:
    conn.execute(f"COPY dim_date TO '{GOLD_DIR}/dim_date.parquet' (FORMAT PARQUET)")
    print("✅ dim_date exported")
except: pass

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*50)
print("📊 TRANSFORMATION COMPLETE!")
print("="*50)

print("\n📈 Record counts:")
tables = {
    "dim_customers": "SELECT COUNT(*) FROM dim_customers",
    "dim_accounts": "SELECT COUNT(*) FROM dim_accounts",
    "fact_transactions": "SELECT COUNT(*) FROM fact_transactions"
}

for name, query in tables.items():
    try:
        count = conn.execute(query).fetchone()[0]
        print(f"  {name}: {count:,}")
    except:
        print(f"  {name}: 0")

conn.close()
print(f"\n✅ Database: banking.duckdb")
print(f"📁 Gold: {GOLD_DIR}/")