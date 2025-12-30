import os
import requests

# Enable debug file writing by service (if used by same process) - not necessary for external request but set for completeness
os.environ['API_DEBUG'] = '1'

url = "https://jetwebapp-api-dev-e4bpepgaeaaxgecr.centralindia-01.azurewebsites.net/api/Users/forgot-password"
payload = {"email": "sohailone@yopmail.com"}

print('Posting to', url)
try:
    r = requests.post(url, json=payload, timeout=15)
    print('STATUS', r.status_code)
    print('HEADERS', dict(r.headers))
    print('TEXT', repr(r.text[:1000]))
except Exception as e:
    print('EXCEPTION', str(e))
