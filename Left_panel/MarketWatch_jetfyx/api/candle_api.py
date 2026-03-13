import requests
from datetime import datetime, timedelta

BASE_URL = "https://quotesdata.jetfyx.com/v2/aggs/ticker"

# Map UI interval labels → API multiplier + timespan
_INTERVAL_MAP = {
    "1m":  ("1",  "minute"),
    "5m":  ("5",  "minute"),
    "15m": ("15", "minute"),
    "1h":  ("1",  "hour"),
    "4h":  ("4",  "hour"),
    "1d":  ("1",  "day"),
}


def get_candles(symbol: str, interval: str = "1m", days_back: int = 40) -> list[dict]:
    """
    Fetch OHLCV candle data for a symbol from the JetFyX quotes API.

    Parameters
    ----------
    symbol    : e.g. "XAUUSD", "EURUSD"
    interval  : one of "1m","5m","15m","1h","4h","1d"
    days_back : how many calendar days of history to request (default 40)

    Returns
    -------
    list of dicts with keys: time, open, high, low, close, volume
    """
    multiplier, timespan = _INTERVAL_MAP.get(interval, ("1", "minute"))

    end_dt   = datetime.today()
    start_dt = end_dt - timedelta(days=days_back)

    start = start_dt.strftime("%Y-%m-%d")
    end   = end_dt.strftime("%Y-%m-%d")

    url = (
        f"{BASE_URL}/C:{symbol}/range/{multiplier}/{timespan}"
        f"/{start}/{end}?adjusted=true&sort=asc&limit=50000"
    )

    try:
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data    = response.json()
            results = data.get("results", [])

            candles = []
            for r in results:
                candles.append({
                    "time":   r["t"],          # milliseconds epoch
                    "open":   r["o"],
                    "high":   r["h"],
                    "low":    r["l"],
                    "close":  r["c"],
                    "volume": r.get("v", 0),
                })
            return candles

        else:
            print(f"[candle_api] HTTP {response.status_code} for {symbol} — {response.text[:200]}")

    except Exception as e:
        print(f"[candle_api] Error fetching {symbol}: {e}")

    return []