import socket
import sys

# The URL to test (without protocol)
host = "jetwebapp-api-dev-e4bpepgaeaaxgecr.centralindia-01.azurewebsites.net"

print(f"Testing DNS resolution for: {host}")
try:
    ip = socket.gethostbyname(host)
    print(f"DNS resolved: {host} -> {ip}")
except Exception as e:
    print(f"DNS resolution failed for {host}: {e}")
    sys.exit(1)

print("Attempting to connect to /hubs/market endpoint...")
import requests
url = f"https://{host}/hubs/market"
try:
    resp = requests.get(url, timeout=5)
    print(f"HTTP status: {resp.status_code}")
    print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"HTTP request failed: {e}")
