import os
import asyncio
import json
import websockets
from datetime import datetime, timezone
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
API_KEY = os.getenv("SUPABASE_API_KEY")
WS_URL = SUPABASE_URL.replace("https://", "wss://") + "/realtime/v1/websocket?apikey=" + API_KEY

BRONZE_DIR = "data/bronze"
TABLES = ["customers", "accounts", "transactions"]

def save_to_parquet(table_name: str, event_type: str, record: dict):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    filename = f"{BRONZE_DIR}/{table_name}_{timestamp}.parquet"
    
    print(f"\n[CDC EVENT] Table: {table_name} | Event: {event_type}")
    print(f"[CDC DATA] {json.dumps(record, indent=2)}")
    
    data = {
        "table_name": table_name,
        "operation": event_type,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "data": json.dumps(record),
    }
    
    table = pa.table({k: [v] for k, v in data.items()})
    pq.write_table(table, filename)
    print(f"[{table_name}] {event_type} -> {filename}\n")

async def listen_cdc():
    print(f"Connecting to Supabase Realtime...")
    
    async with websockets.connect(WS_URL) as websocket:
        print("✅ WebSocket Connected!")
        
        # Subscribe ke semua tabel
        for table in TABLES:
            subscribe_msg = {
                "topic": f"realtime:public:{table}",
                "event": "phx_join",
                "payload": {
                    "config": {
                        "postgres_changes": [{
                            "event": "*",
                            "schema": "public",
                            "table": table
                        }]
                    }
                },
                "ref": str(TABLES.index(table) + 1)
            }
            await websocket.send(json.dumps(subscribe_msg))
            print(f"📤 Subscribed to: {table}")
        
        print("\n⏳ Menunggu perubahan data (Ctrl+C untuk stop)...\n")
        
        # Listen untuk pesan
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Cek apakah ini event postgres_changes
                if data.get("event") == "postgres_changes":
                    payload = data.get("payload", {})
                    table = payload.get("data", {}).get("table")
                    event_type = payload.get("data", {}).get("type")
                    record = payload.get("data", {}).get("record", {})
                    
                    if table and event_type and record:
                        save_to_parquet(table, event_type, record)
                        
            except json.JSONDecodeError:
                pass

async def main():
    while True:
        try:
            await listen_cdc()
        except Exception as e:
            print(f"❌ Error: {e}")
            print("🔄 Reconnecting in 3 seconds...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")