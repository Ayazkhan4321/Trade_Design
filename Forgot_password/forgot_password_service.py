"""Forgot password API service.

Encapsulates network calls and response validation for the /User/forgot-password endpoint.
This keeps the API logic and validation isolated from UI/controller code and matches
patterns used elsewhere in the project (retries, timeouts, pydantic validation).
"""
from typing import Optional, Tuple
import logging

import requests
from pydantic import BaseModel, ValidationError
import re


def _is_valid_email(email: str) -> bool:
    """Simple email format check without pulling extra dependencies during import.

    We deliberately avoid pydantic's EmailStr because it requires the separate
    `email-validator` package which isn't always present in minimal test envs.
    This function checks a conservative pattern sufficient for client-side validation.
    """
    if not isinstance(email, str) or not email:
        return False
    # Basic pattern: something@something.suffix
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from api.config import API_USER_FORGOT_PASSWORD
from api.config import API_TIMEOUT, API_VERIFY_TLS, API_RETRIES
from settings import feature_flags as feature_flags
from Forgot_password import messages as messages

logger = logging.getLogger(__name__)


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    # Be permissive: many APIs return {"message": "..."} or {"data": {...}}
    message: Optional[str] = None
    data: Optional[dict] = None


def _get_session(retries: int = API_RETRIES) -> requests.Session:
    session = requests.Session()
    # Add User-Agent header required by backend
    session.headers.update({"User-Agent": "JetFyXDesktop/1.0"})
    backoff = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=(429, 502, 503, 504),
        allowed_methods=("POST", "GET", "PUT", "DELETE", "OPTIONS"),
    )
    adapter = HTTPAdapter(max_retries=backoff)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def send_reset_link(email: str) -> Tuple[bool, str, bool]:
    """Send the forgot-password request to the server.

    Returns: (success: bool, message: str, retryable: bool)
    - `retryable` is True when the failure is transient and the client can offer a retry (timeout, 5xx, 429, etc.).
    """
    # Validate email client-side using a lightweight check
    if not _is_valid_email(email):
        return False, "Please enter a valid email address.", False

    url = API_USER_FORGOT_PASSWORD
    payload = {"email": email}
    session = _get_session()

    try:
        logger.debug("POST %s payload=%s", url, payload)
        print(f"\n[DEBUG] Request Headers: {dict(session.headers)}")
        resp = session.post(url, json=payload, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
        logger.debug("Status code: %s", resp.status_code)

        # Log response body for troubleshooting (do not include sensitive fields)
        try:
            body_text = resp.text
            logger.debug("Forgot-password response body: %s", body_text)
        except Exception:
            logger.debug("Could not read response text for logging")

        # Handle common status codes
        if resp.status_code == 400:
            # client error - don't offer retry
            # try to include server-provided message
            try:
                body_json = resp.json()
                msg = body_json.get("message") or "Invalid request. Please check the email and try again."
            except Exception:
                msg = "Invalid request. Please check the email and try again."
            return False, msg, False

        if resp.status_code == 404:
            # Return explicit 'not registered' message per request (clear messaging)
            return False, messages.MSG_NOT_REGISTERED, False

        if resp.status_code == 429:
            return False, "Too many requests. Please try again later.", True

        if resp.status_code >= 500:
            return False, "Server error. Please try again later.", True

        # Accept all 2xx as success
        if not (200 <= resp.status_code < 300):
            # attempt to include server message
            try:
                body_json = resp.json()
                msg = body_json.get("message") or "Unexpected error occurred."
            except Exception:
                msg = "Unexpected error occurred."
            return False, msg, True

        # Parse JSON
        try:
            body = resp.json()
        except ValueError:
            logger.exception("Failed to parse JSON from forgot-password response")
            msg = messages.MSG_EXPLICIT_SENT_TEMPLATE.format(email=email) if feature_flags.ALLOW_EXPLICIT_USER_MESSAGES else messages.MSG_SENT
            return True, msg, False

        # Try to validate structure with pydantic (best-effort)
        try:
            validated = ForgotPasswordResponse.parse_obj(body)
        except ValidationError:
            logger.debug("Response did not match Expected schema; continuing with raw body")
            validated = ForgotPasswordResponse(message=body.get("message") if isinstance(body, dict) else None, data=body if isinstance(body, dict) else None)

        message = validated.message or (validated.data or {}).get("message") if isinstance(validated.data, dict) else None
        # fallback to generic message; return clear sent message by default
        if message:
            # If the backend supplies a message, use it; otherwise use our clear message
            pass
        else:
            message = messages.MSG_EXPLICIT_SENT_TEMPLATE.format(email=email) if feature_flags.ALLOW_EXPLICIT_USER_MESSAGES else messages.MSG_SENT
        return True, message, False

    except requests.exceptions.Timeout:
        logger.warning("Forgot-password request timed out for %s", email)
        return False, "Request timed out. Please check your network and try again.", True

    except requests.exceptions.ConnectionError:
        logger.warning("Unable to connect to forgot-password endpoint")
        return False, "Unable to connect to server. Please try again later.", True

    except Exception:
        logger.exception("Unexpected error during forgot-password request")
        return False, "Unexpected error occurred.", True