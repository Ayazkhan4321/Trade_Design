import requests

class ApiClient:
    def __init__(self, base=None):
        self.base = base or "https://quotesdata.jetfyx.com"

    def get_aggs(self, symbol="XAUUSD", start="2026-02-01", end="2026-03-03", interval="1"):
        # interval = aggregation window (minutes)
        url = f"{self.base}/v2/aggs/ticker/C:{symbol}/range/{interval}/minute/{start}/{end}"
        params = {"adjusted": "true", "sort": "asc", "limit": 50000}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()