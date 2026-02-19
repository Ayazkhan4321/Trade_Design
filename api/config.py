# api/config.py

# api/config.py
# This module contains API endpoint constants and related network defaults.
# The API base URL and network defaults such as timeouts/retries are kept here
# for simplicity; we can move them back to env-driven settings later if needed.

API_BASE_URL = "https://jetwebapp-api-dev-e4bpepgaeaaxgecr.centralindia-01.azurewebsites.net/api"
import re

# Hub/base URL (useful for building websocket/WSS URLs by stripping `/api`)
HUB_BASE_URL = re.sub(r"/api/?$", "", API_BASE_URL, flags=re.IGNORECASE)

# SignalR/WebSocket Hub endpoints
HUB_ORDERS = f"{HUB_BASE_URL}/hubs/orders"
HUB_MARKET_DATA = f"{HUB_BASE_URL}/hubs/market"

# Network & security defaults (used when calling services)
API_VERIFY_TLS = True  # Set False only for local testing; NEVER disable in production
API_TIMEOUT = 10  # seconds
API_RETRIES = 3  # number of retry attempts for transient errors

# Top-level endpoints (keep endpoints in one place for easy updates)
API_AUTH_LOGIN = f"{API_BASE_URL}/Auth/login"
API_USER_FORGOT_PASSWORD = f"{API_BASE_URL}/Users/forgot-password"
API_ACCOUNTS_CREATE = f"{API_BASE_URL}/Users/register"
API_ACCOUNTS_SEND = f"{API_BASE_URL}/Users/send-otp-by-email"
# The verify endpoint may require the user id in the path. Provide a templated
# endpoint and a fallback non-id endpoint. Use the template when a user id is
# available from account creation.
API_ACCOUNTS_VERIFY_TEMPLATE = f"{API_BASE_URL}/Users/{{UserId}}/verify-otp"
#API_ACCOUNTS_VERIFY = f"{API_BASE_URL}/Users/verify-otp"
API_COUNTRIES = f"{API_BASE_URL}/Countries"
API_ORDERS = f"{API_BASE_URL}/Orders"
API_ORDERS_ITEM = f"{API_BASE_URL}/Orders/{{orderId}}"
API_ORDERS_CLOSE = API_ORDERS_ITEM
API_ORDERS_HISTORY = f"{API_BASE_URL}/Orders/history/{{accountId}}"
API_CLIENT_MESSAGES_ACCOUNT = f"{API_BASE_URL}/client/Messages/account/{{accountId}}"
API_FAVOURITE_WATCHLIST_TEMPLATE = f"{API_BASE_URL}/favourite-watchlist-symbols?accountId={{accountId}}"
API_ORDERS_BULK_CLOSE = f"{API_BASE_URL}/Orders/bulk-close"



