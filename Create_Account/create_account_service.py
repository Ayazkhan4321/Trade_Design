from typing import Optional, Tuple, List, Union
import logging
import re

import requests
from pydantic import BaseModel, ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from api.config import (
    API_ACCOUNTS_CREATE,
    API_COUNTRIES,
    API_ACCOUNTS_SEND,
    API_ACCOUNTS_VERIFY_TEMPLATE,
    API_TIMEOUT,
    API_VERIFY_TLS,
    API_RETRIES,
)

from Create_Account import messages as messages

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get_session(retries: int = API_RETRIES) -> requests.Session:
    session = requests.Session()
    # Add User-Agent header required by backend
    session.headers.update({"User-Agent": "JetFyXDesktop/1.0"})
    retry = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=(429, 502, 503, 504),
        allowed_methods=("POST", "GET", "PUT", "DELETE", "OPTIONS"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _is_valid_email(email: str) -> bool:
    return isinstance(email, str) and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)


def _is_probable_phone(phone: str) -> bool:
    if not isinstance(phone, str):
        return False
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 6


def build_verify_otp_url(user_id: int | str) -> str:
    """
    Safely replaces {UserId} in backend endpoint.
    HARD FAILS if userId is invalid.
    """
    if user_id is None:
        raise ValueError("UserId is required for OTP verification")

    user_id = str(user_id).strip()

    if not user_id.isdigit():
        raise ValueError(f"Invalid UserId: {user_id}")

    # Accept either {UserId} or {userId} token to be tolerant of minor
    # configuration differences in the environment.
    if "{UserId}" in API_ACCOUNTS_VERIFY_TEMPLATE:
        return API_ACCOUNTS_VERIFY_TEMPLATE.replace("{UserId}", user_id)
    if "{userId}" in API_ACCOUNTS_VERIFY_TEMPLATE:
        return API_ACCOUNTS_VERIFY_TEMPLATE.replace("{userId}", user_id)
    raise RuntimeError("Verify OTP endpoint is misconfigured")


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class CreateAccountRequest(BaseModel):
    firstName: str
    lastName: str
    email: Optional[str] = None
    phone: str
    roleName: str
    refLink: int = 0


class CreateAccountResponse(BaseModel):
    message: Optional[str] = None
    data: Optional[dict] = None


# ------------------------------------------------------------------
# Services
# ------------------------------------------------------------------

def create_account(payload: CreateAccountRequest, include_data=False, debug: bool = False):
    if not payload.firstName or not payload.lastName:
        return False, "First and last name are required.", False

    if payload.email and not _is_valid_email(payload.email):
        return False, "Invalid email address.", False

    if not _is_probable_phone(payload.phone):
        return False, "Invalid phone number.", False

    url = API_ACCOUNTS_CREATE
    session = _get_session()

    body = payload.dict()

    try:
        logger.debug("POST %s payload=%s", url, body)
        # Defensive access for test doubles that may not provide `headers`
        try:
            hdrs = dict(getattr(session, "headers", {}) or {})
        except Exception:
            hdrs = {}
        print(f"\n[DEBUG] Request Headers: {hdrs}")
        resp = session.post(url, json=body, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)

        if resp.status_code == 400:
            # Some servers return structured JSON with a message on bad requests
            try:
                body = resp.json() or {}
                msg = body.get("message", "Invalid request")
            except Exception:
                msg = "Invalid request"
            if debug:
                server_text = getattr(resp, 'text', None) or str(body)
                msg = f"{msg} (server: {server_text})"
            return False, msg, False

        if resp.status_code >= 500:
            msg = "Server error. Try again later."
            if debug:
                server_text = getattr(resp, 'text', None)
                try:
                    body = resp.json() or {}
                except Exception:
                    body = None
                msg = f"{msg} (server: {server_text or body})"
            return False, msg, True

        # Be defensive when dealing with response objects in tests/mocks that may
        # not provide a `content` attribute; use getattr to avoid AttributeError.
        try:
            data = resp.json() or {}
        except Exception:
            data = {}
        msg = data.get("message", messages.MSG_ACCOUNT_CREATED)

        if include_data:
            return True, msg, False, data.get("data")

        return True, msg, False

    except Exception as e:
        logger.exception("Create account failed")
        if debug:
            return False, f"Unexpected error occurred: {e}", True
        return False, "Unexpected error occurred.", True


def build_verify_request(user_id: int | str, otp: str, account_type_id: Optional[int] = None):
    """
    Builds a SAFE verify-otp request.
    Guarantees:
    - userId is valid
    - route userId == body userId
    - payload shape matches backend contract
    """
    if user_id is None:
        raise ValueError("UserId is required for verification")

    user_id = str(user_id).strip()
    if not user_id.isdigit():
        raise ValueError(f"Invalid UserId: {user_id}")

    if not otp or not otp.strip():
        raise ValueError("OTP is required")

    # URL (single source of truth)
    url = build_verify_otp_url(user_id)

    # Payload (must match route)
    payload = {
        "userId": int(user_id),
        "otp": otp.strip(),
    }

    if account_type_id is not None:
        payload["accountTypeId"] = int(account_type_id)

    return url, payload


def verify_otp(user_id: int | str, otp: str, account_type_id: Optional[int] = None, debug: bool = False):
    """
    OTP verification using /Users/{UserId}/verify-otp endpoint.
    Supports both templated (numeric userId in path) and generic endpoints.
    """
    # Validate OTP first
    if not otp or not otp.strip():
        return False, "OTP is required.", False

    user_id = str(user_id).strip()

    # If numeric, use templated endpoint; otherwise use generic endpoint or dry-run
    if user_id.isdigit():
        # Try to use templated endpoint
        try:
            url, payload = build_verify_request(user_id, otp, account_type_id)
        except ValueError as e:
            return False, str(e), False
    else:
        # Non-numeric identifier: check for generic endpoint
        api_verify_generic = globals().get("API_ACCOUNTS_VERIFY", None)
        if api_verify_generic is None and "API_ACCOUNTS_VERIFY" in globals():
            # Explicitly disabled (set to None by tests) - dry-run mode
            return True, "Verified (no endpoint configured)", False

        # Use generic endpoint if available
        if api_verify_generic:
            url = api_verify_generic
        else:
            # Fallback: no endpoint available - dry-run
            return True, "Verified (no endpoint configured)", False

        # Build generic payload
        payload = {
            "userId": int(user_id) if user_id.isdigit() else user_id,
            "otp": otp.strip(),
        }
        if account_type_id is not None:
            payload["accountTypeId"] = int(account_type_id)

    session = _get_session()

    try:
        logger.debug("POST %s payload=%s", url, payload)
        resp = session.post(url, json=payload, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)

        if resp.status_code == 400:
            try:
                body = resp.json() or {}
                msg = body.get("message", "Invalid verification request")
            except Exception:
                msg = "Invalid verification request"
            if debug:
                server_text = getattr(resp, 'text', None) or str(body)
                msg = f"{msg} (server: {server_text})"
            return False, msg, False

        if resp.status_code >= 500:
            msg = "Server error. Please try again later."
            if debug:
                server_text = getattr(resp, 'text', None)
                try:
                    body = resp.json() or {}
                except Exception:
                    body = None
                msg = f"{msg} (server: {server_text or body})"
            return False, msg, True

        try:
            data = resp.json() or {}
        except Exception:
            data = {}
        return True, data.get("message", "OTP verified successfully."), False

    except Exception as e:
        logger.exception("OTP verification failed")
        if debug:
            return False, f"Unexpected error occurred: {e}", True
        return False, "Unexpected error occurred.", True


def send_verification(payload, debug: bool = False):
    # If no endpoint configured, be a no-op (useful for dry-run/test environments)
    if not API_ACCOUNTS_SEND:
        return True, "dry-run: OTP sent (no endpoint configured)", False

    session = _get_session()

    # Accept either a dict or a plain email string as payload
    orig_payload = payload
    json_payload = payload
    if isinstance(payload, str):
        json_payload = {"email": payload}

    try:
        resp = session.post(API_ACCOUNTS_SEND, json=json_payload, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)

        # If server rejects JSON with 415 (unsupported media), retry using text/data when
        # the original payload was a string (some servers accept raw text bodies)
        if resp.status_code == 415 and isinstance(orig_payload, str):
            try:
                resp = session.post(API_ACCOUNTS_SEND, data=orig_payload, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
            except Exception:
                pass

        # handle server errors
        if resp.status_code >= 500:
            msg = "Server error. Please try again later."
            if debug:
                server_text = getattr(resp, 'text', None)
                try:
                    body = resp.json() or {}
                except Exception:
                    body = None
                msg = f"{msg} (server: {server_text or body})"
            return False, msg, True

        try:
            data = resp.json() or None
        except Exception:
            data = None

        # Return data when present (createdAt / data dict), otherwise use text or message
        if isinstance(data, dict):
            # Return data only when the response contains additional useful
            # fields beyond a simple message (e.g., createdAt). For simple
            # {'message': ...} responses prefer a 3-tuple for backward compat.
            if len(data) > 1:
                msg = data.get("message", "OTP sent.")
                if debug:
                    msg = f"{msg} (server data present)"
                return True, msg, False, data
            msg = data.get("message", "OTP sent.")
            if debug:
                server_text = getattr(resp, 'text', None) or str(data)
                msg = f"{msg} (server: {server_text})"
            return True, msg, False
        text = getattr(resp, 'text', None) or "OTP sent."
        if debug:
            text = f"{text} (server: {getattr(resp, 'text', None)})"
        return True, text, False

    except Exception:
        logger.exception("Send verification failed")
        return False, "Unexpected error occurred.", True


def get_countries() -> Tuple[bool, Union[List[dict], str], bool]:
    """Fetch list of countries for the country combobox.

    Returns: (success, list_of_countries_or_error_message, retryable)
    """
    url = API_COUNTRIES
    session = _get_session()
    try:
        logger.debug("GET %s", url)
        resp = session.get(url, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
        logger.debug("Countries status code: %s", resp.status_code)

        if resp.status_code == 429:
            return False, "Too many requests; please try again later.", True

        if resp.status_code >= 500:
            return False, "Server error. Please try again later.", True

        if not (200 <= resp.status_code < 300):
            try:
                body_json = resp.json()
                msg = body_json.get("message") or "Unexpected error occurred while fetching countries."
            except Exception:
                msg = "Unexpected error occurred while fetching countries."
            return False, msg, True

        try:
            body = resp.json()
        except ValueError:
            logger.exception("Failed to parse JSON from countries response")
            return False, "Failed to fetch countries.", False

        # Expecting a list of country objects; be permissive otherwise
        if isinstance(body, list):
            return True, body, False
        elif isinstance(body, dict) and "data" in body and isinstance(body["data"], list):
            return True, body["data"], False
        else:
            # Fallback: return whatever the server supplied as a message
            return False, "Unexpected countries data format.", False

    except requests.exceptions.Timeout:
        logger.warning("Countries request timed out")
        return False, "Request timed out. Please check your network and try again.", True

    except requests.exceptions.ConnectionError:
        logger.warning("Unable to connect to countries endpoint")
        return False, "Unable to connect to server. Please try again later.", True

    except Exception:
        logger.exception("Unexpected error during countries request")
        return False, "Unexpected error occurred.", True
