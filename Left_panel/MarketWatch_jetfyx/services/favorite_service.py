def remove_favorite(favorite_id: int):
    """Remove a symbol from the user's favorite watch list by FavouriteId."""
    url = f"{API_FAVORITE_WATCHLIST}/{favorite_id}"
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "User-Agent": "JetFyXDesktop/1.0"
    }
    response = requests.delete(url, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
    response.raise_for_status()
    return response.status_code == 204
import requests
from MarketWatch_jetfyx.api.config import API_FAVORITE_WATCHLIST, API_TIMEOUT, API_VERIFY_TLS
from accounts.auth_service import get_token


def add_favorite(symbol: str, account_id: int):
    """Add a symbol to the user's favorite watch list."""
    url = API_FAVORITE_WATCHLIST
    payload = {"symbol": symbol, "accountId": account_id}
    print(f"[DEBUG] add_favorite payload: {payload}")
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
        "User-Agent": "JetFyXDesktop/1.0"
    }
    response = requests.post(url, json=payload, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
    print(f"[DEBUG] add_favorite response: {response.status_code} {response.text}")
    response.raise_for_status()
    return response.json()


def get_favorites(account_id: int):
    """Get the user's favorite watch list."""
    url = f"{API_FAVORITE_WATCHLIST}?accountId={account_id}"
    print(f"[DEBUG] get_favorites will call: {url}")
    headers = {
        "Authorization": f"Bearer {get_token()}"
    }
    response = requests.get(url, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
    response.raise_for_status()
    return response.json()
