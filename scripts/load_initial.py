import os
import json
from datetime import datetime, timezone
from supabase import create_client
from dotenv import load_dotenv
import pyarrow as pa
import pyarrow.parquet as pq

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
BRONZE_DIR = "data/bronze"

supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

TABLES = ["customers", "accounts", "transactions"]

def save_to_parquet(table_name: str, record: dict):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    filename = f"{BRONZE_DIR}/{table_name}_initial_{timestamp}.parquet"
    
    data = {
        "table_name": table_name,
        "operation": "INSERT",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "data": json.dumps(record),
    }
    
    table = pa.table({k: [v] for k, v in data.items()})
    pq.write_table(table, filename)
    print(f"✅ {table_name}: {record.get('customer_id') or record.get('account_id') or record.get('transaction_id')} -> {filename}")

def load_all_data():
    print("📥 Loading all data from Supabase...")
    
    for table in TABLES:
        print(f"\n📋 Fetching {table}...")
        
        # Ambil semua data
        result = supabase.table(table).select('*').execute()
        data = result.data
        
        print(f"  ✅ Found {len(data)} records")
        
        # Simpan ke Bronze
        for record in data:
            save_to_parquet(table, record)
    
    print("\n✅ Initial load complete!")

if __name__ == "__main__":
    load_all_data()