import websocket
import ssl

url = "wss://jetwebapp-api-dev-e4bpepgaeaaxgecr.centralindia-01.azurewebsites.net/hubs/market"

print(f"Testing WebSocket connection to: {url}")
try:
    ws = websocket.create_connection(url, sslopt={"cert_reqs": ssl.CERT_NONE}, timeout=5)
    print("WebSocket connection established!")
    ws.close()
except Exception as e:
    print(f"WebSocket connection failed: {e}")
