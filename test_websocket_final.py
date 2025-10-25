# test_websocket_final.py
import asyncio
import websockets
import json
import sys

async def test_connection():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYwNjg4Mjg5LCJpYXQiOjE3NjA2ODQ2ODksImp0aSI6IjU5MWZiMjA1ZTVhYTQ2MmRhMzdjOTY0ODY1Yjg4ZDY0IiwidXNlcl9pZCI6MX0.e7mRFOwTW0kCfSVyO15GStrkqzsc3DMcHuzMuyPqE5Y"
    uri = f"ws://localhost:8000/ws/socket-server/?token={token}"
    
    try:
        print("🔄 Testing WebSocket connection...")
        print(f"URL: {uri}")
        
        async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Subscribe to updates
            subscribe_msg = {"type": "subscribe_products"}
            await websocket.send(json.dumps(subscribe_msg))
            print(f"📤 Sent subscription: {subscribe_msg}")
            
            # Wait for subscription confirmation or any initial message
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No immediate response after subscription, that's OK")
            
            print("✅ Connection test completed successfully!")
            print("💡 You can now send/receive messages like:")
            print('   - {"type": "product_update", "action": "create", "product": {...}}')
            print('   - {"type": "subscribe_inventory"}')
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed with status code: {e.status_code}")
        print(f"❌ Response headers: {e.headers}")
    except ConnectionRefusedError as e:
        print(f"❌ Connection refused. Make sure Daphne server is running on ws://localhost:8000")
        print(f"❌ Error details: {e}")
    except websockets.exceptions.InvalidHandshake as e:
        print(f"❌ Invalid handshake: {e}")
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())