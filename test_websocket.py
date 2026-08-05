# test_websocket.py
import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
WS_URL = SUPABASE_URL.replace("https://", "wss://") + "/realtime/v1/websocket?apikey=" + API_KEY

async def test():
    print(f"Connecting...")
    
    async with websockets.connect(WS_URL) as websocket:
        print("✅ Connected!")
        
        # Subscribe ke customers
        subscribe_msg = {
            "topic": "realtime:public:customers",
            "event": "phx_join",
            "payload": {
                "config": {
                    "postgres_changes": [{
                        "event": "*",
                        "schema": "public",
                        "table": "customers"
                    }]
                }
            },
            "ref": "1"
        }
        
        await websocket.send(json.dumps(subscribe_msg))
        print("📤 Subscribed!")
        
        # Listen
        async for msg in websocket:
            print(f"📩 {msg[:300]}")

asyncio.run(test())