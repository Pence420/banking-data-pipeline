from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "/Users/joshuats/banking-data-pipeline/banking.duckdb"

# ============================================================
# HELPER: Safe query (PASTI return DataFrame)
# ============================================================
def safe_query(query):
    try:
        conn = duckdb.connect(DB_PATH)
        df = conn.execute(query).fetchdf()
        conn.close()
        return df
    except Exception as e:
        print(f"⚠️ Query error: {e}")
        return pd.DataFrame()  # PASTI return DataFrame kosong, bukan None

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/api/customers")
def get_customers():
    df = safe_query("SELECT * FROM dim_customers")
    return df.to_dict('records')

@app.get("/api/accounts")
def get_accounts():
    df = safe_query("SELECT * FROM dim_accounts WHERE is_current_record = TRUE")
    return df.to_dict('records')

@app.get("/api/transactions")
def get_transactions():
    df = safe_query("SELECT * FROM fact_transactions LIMIT 100")
    return df.to_dict('records')

@app.get("/api/metrics")
def get_metrics():
    conn = duckdb.connect(DB_PATH)
    try:
        customers = conn.execute("SELECT COUNT(*) FROM dim_customers").fetchone()[0]
    except:
        customers = 0
    
    try:
        accounts = conn.execute("SELECT COUNT(*) FROM dim_accounts WHERE is_current_record = TRUE").fetchone()[0]
    except:
        accounts = 0
    
    try:
        transactions = conn.execute("SELECT COUNT(*) FROM fact_transactions").fetchone()[0]
    except:
        transactions = 0
    
    try:
        total_volume = conn.execute("SELECT SUM(amount) FROM fact_transactions").fetchone()[0]
        if total_volume is None:
            total_volume = 0
    except:
        total_volume = 0
    
    conn.close()
    
    return {
        "total_customers": int(customers),
        "total_accounts": int(accounts),
        "total_transactions": int(transactions),
        "total_volume": float(total_volume)
    }

@app.get("/api/loyalty")
def get_loyalty():
    df = safe_query("""
        SELECT loyalty_tier, COUNT(*) as count 
        FROM dim_customers 
        GROUP BY loyalty_tier
    """)
    return df.to_dict('records')

@app.get("/api/status")
def get_status():
    df = safe_query("""
        SELECT status, COUNT(*) as count 
        FROM dim_customers 
        GROUP BY status
    """)
    return df.to_dict('records')

if __name__ == "__main__":
    import uvicorn
    print("🚀 Backend running at http://localhost:8000")
    print(f"📁 Database: {DB_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=8000)