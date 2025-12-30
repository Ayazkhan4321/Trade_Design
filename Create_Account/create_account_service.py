"""Create Account API service.

Encapsulates network calls for the /Accounts/CreateAccount and /Countries endpoints.
Follows the same error-handling and retry pattern used by other services in the repo.
"""
from typing import Optional, Tuple, List, Union
import logging

import requests
from pydantic import BaseModel, ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

from api.config import API_ACCOUNTS_CREATE, API_COUNTRIES, API_ACCOUNTS_SEND, API_ACCOUNTS_VERIFY
from api.config import API_TIMEOUT, API_VERIFY_TLS, API_RETRIES
from Create_Account import messages as messages

logger = logging.getLogger(__name__)


def _is_valid_email(email: str) -> bool:
    if not isinstance(email, str) or not email:
        return False
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None


def _is_probable_phone(phone: str) -> bool:
    if not isinstance(phone, str) or not phone:
        return False
    # allow +, digits, spaces, hyphens; require at least 6 digits
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 6


class CreateAccountRequest(BaseModel):
    firstName: str
    lastName: str
    email: Optional[str] = None
    phone: str
    accountTypeID: int
    creationType: str
    referralCode: Optional[str] = None
    country: Optional[dict] = None


class CreateAccountResponse(BaseModel):
    message: Optional[str] = None
    data: Optional[dict] = None


def _get_session(retries: int = API_RETRIES) -> requests.Session:
    session = requests.Session()
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


def create_account(payload: CreateAccountRequest, include_data: bool = False) -> Tuple[bool, str, bool]:
    """Send account creation request.

    Returns tuple (success, message, retryable).
    If `include_data` is True, a fourth return value containing the server
    'data' dict (if present) will be appended for convenience.
    """
    # Basic client-side validation
    if not payload.firstName or not payload.lastName:
        return False, "First and last name are required.", False

    if payload.email and not _is_valid_email(payload.email):
        return False, "Please enter a valid email address.", False

    if not _is_probable_phone(payload.phone):
        return False, "Please enter a valid phone number.", False

    if payload.creationType not in ("Live", "Demo"):
        return False, "Invalid account creation type.", False

    if not isinstance(payload.accountTypeID, int):
        return False, "Invalid account type.", False

    url = API_ACCOUNTS_CREATE
    session = _get_session()
    body = payload.dict()
    # tidy country value: if dict, include only expected keys
    if isinstance(body.get("country"), dict):
        # keep name and dial_code if present
        country = body["country"]
        body["country"] = {k: country.get(k) for k in ("name", "dial_code", "code") if k in country}

    try:
        logger.debug("POST %s payload=%s", url, body)
        resp = session.post(url, json=body, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
        logger.debug("Status code: %s", resp.status_code)

        try:
            body_text = resp.text
            logger.debug("Create-account response body: %s", body_text)
        except Exception:
            logger.debug("Could not read response text for logging")

        if resp.status_code == 400:
            try:
                body_json = resp.json()
                msg = body_json.get("message") or "Invalid request. Please check the details and try again."
            except Exception:
                msg = "Invalid request. Please check the details and try again."
            return False, msg, False

        if resp.status_code == 429:
            return False, "Too many requests; please try again later.", True

        if resp.status_code >= 500:
            return False, "Server error. Please try again later.", True

        if not (200 <= resp.status_code < 300):
            try:
                body_json = resp.json()
                msg = body_json.get("message") or "Unexpected error occurred."
            except Exception:
                msg = "Unexpected error occurred."
            return False, msg, True

        try:
            body = resp.json()
        except ValueError:
            logger.exception("Failed to parse JSON from create-account response")
            return True, messages.MSG_ACCOUNT_CREATED, False

        # If server supplied an explicit message, prefer it
        if isinstance(body, dict) and body.get("message"):
            # Try to also return data when present
            data = body.get("data") if isinstance(body.get("data"), dict) else None
            if include_data:
                return True, body.get("message"), False, data
            return True, body.get("message"), False

        try:
            validated = CreateAccountResponse.parse_obj(body)
        except ValidationError:
            logger.debug("Response did not match Expected schema; continuing with raw body")
            validated = CreateAccountResponse(message=body.get("message") if isinstance(body, dict) else None, data=body if isinstance(body, dict) else None)

        message = validated.message or (validated.data or {}).get("message") if isinstance(validated.data, dict) else None
        if message:
            if include_data:
                return True, message, False, (validated.data if isinstance(validated.data, dict) else None)
            return True, message, False
        else:
            if include_data:
                return True, messages.MSG_ACCOUNT_CREATED, False, (validated.data if isinstance(validated.data, dict) else None)
            return True, messages.MSG_ACCOUNT_CREATED, False

    except requests.exceptions.Timeout:
        logger.warning("Create-account request timed out")
        return False, "Request timed out. Please check your network and try again.", True

    except requests.exceptions.ConnectionError:
        logger.warning("Unable to connect to create-account endpoint")
        return False, "Unable to connect to server. Please try again later.", True

    except Exception:
        logger.exception("Unexpected error during create-account request")
        return False, "Unexpected error occurred.", True


def verify_otp(identifier: str, code: str, account_type_id: Optional[int] = None) -> Tuple[bool, str, bool]:
    """Verify OTP code for a newly-created account.

    Sends payload containing the otp and the user/account identifier and
    optionally the accountTypeId. The server expects the body to include
    `userId` (or `identifier`), `otp`, and `accountTypeId` when available.

    The function will prefer a templated endpoint if provided in
    `API_ACCOUNTS_VERIFY_TEMPLATE`, but will always include the payload
    fields so the server has the necessary context.

    Returns (success, message, retryable)
    """
    if not isinstance(code, str) or not code.strip():
        return False, "Please enter the verification code.", False

    # Prefer templated endpoint if available and identifier is numeric (user id)
    url = None
    try:
        from api.config import API_ACCOUNTS_VERIFY_TEMPLATE
        if isinstance(identifier, str) and identifier.isdigit():
            url = API_ACCOUNTS_VERIFY_TEMPLATE.format(userId=identifier)
    except Exception:
        # Template not present or formatting failed: fall back
        url = None

    # fallback to generic verify endpoint
    if not url:
        url = API_ACCOUNTS_VERIFY

    if not url:
        # No server endpoint configured; accept any non-empty code
        return True, "Verified.", False

    session = _get_session()
    # Build payload per requested server contract: include userId (when available), otp, accountTypeId
    payload = {}
    if isinstance(identifier, str) and identifier.isdigit():
        # Send userId as numeric when available
        try:
            payload['userId'] = int(identifier)
        except Exception:
            payload['userId'] = identifier
    else:
        payload['identifier'] = identifier

    payload['otp'] = code.strip()
    if account_type_id is not None:
        payload['accountTypeId'] = int(account_type_id)

    try:
        logger.debug("POST %s payload=%s", url, payload)
        resp = session.post(url, json=payload, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)
        logger.debug("Verify status code: %s", getattr(resp, 'status_code', None))

        try:
            status = int(getattr(resp, 'status_code', None))
        except Exception:
            status = getattr(resp, 'status_code', None)

        if status == 400:
            try:
                body_json = resp.json()
                msg = body_json.get("message") or "Invalid code."
            except Exception:
                msg = "Invalid code."
            return False, msg, False

        if status == 429:
            return False, "Too many requests; please try again later.", True

        if isinstance(status, int) and status >= 500:
            return False, "Server error. Please try again later.", True

        if not (isinstance(status, int) and 200 <= status < 300):
            try:
                body_json = resp.json()
                msg = body_json.get("message") or "Unexpected error occurred."
            except Exception:
                msg = "Unexpected error occurred."
            return False, msg, True

        try:
            body = resp.json()
        except ValueError:
            logger.debug("No JSON returned from verify endpoint; assuming success")
            return True, "Verified.", False

        # If the server returned an explicit message, prefer it
        if isinstance(body, dict) and body.get("message"):
            return True, body.get("message"), False

        return True, "Verified.", False

    except requests.exceptions.Timeout:
        logger.warning("Verify request timed out")
        return False, "Request timed out. Please check your network and try again.", True

    except requests.exceptions.ConnectionError:
        logger.warning("Unable to connect to verify endpoint")
        return False, "Unable to connect to server. Please try again later.", True

    except Exception:
        logger.exception("Unexpected error during verify request")
        return False, "Unexpected error occurred.", True


def send_verification(payload: object) -> Tuple[bool, str, bool]:
    """Request the server to send a verification code (OTP).

    The server historically accepted a plain email string (text/plain) instead
    of a JSON object. Accept either a plain string (email), a dict containing
    only an email, or a richer dict and POST using the appropriate content type.

    Returns (success, message, retryable)
    """
    url = API_ACCOUNTS_SEND
    # Normalize payload: allow None, str, or dict
    if payload is None:
        payload = {}

    if not url:
        # No endpoint configured; treat as success (dry-run)
        return True, "Verification code sent (dry-run).", False

    session = _get_session()

    # Determine whether to send as JSON or plain text.
    # Prefer JSON for string payloads (server expects JSON) but be resilient:
    # if the server responds 415 (Unsupported Media Type), retry once with
    # text/plain body containing the email string.
    json_body = None
    text_body = None

    if isinstance(payload, str):
        # Prefer JSON for a plain email string
        json_body = {"email": payload}
    elif isinstance(payload, dict):
        # Send dicts as JSON by default
        json_body = payload
    else:
        # Fallback to sending text
        try:
            text_body = str(payload)
        except Exception:
            json_body = {}

    tried_text = False
    tried_json = bool(json_body is not None)

    def _post_json(pb):
        logger.debug("Send-verification json payload: %s", pb)
        return session.post(url, json=pb, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)

    def _post_text(tb):
        headers = {"Content-Type": "text/plain"}
        logger.debug("Send-verification text payload: %s", tb)
        return session.post(url, data=tb, headers=headers, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)

    try:
        resp = None
        # First attempt: JSON if available, otherwise text
        if json_body is not None:
            logger.debug("POST %s payload=%s (initial=json)", url, json_body)
            resp = _post_json(json_body)
        else:
            logger.debug("POST %s payload=%s (initial=text)", url, text_body)
            resp = _post_text(text_body)

        logger.debug("Send-verification status code: %s", getattr(resp, 'status_code', None))

        # Handle 415 Unsupported Media Type by retrying with the alternate format once
        try:
            status = int(getattr(resp, 'status_code', None))
        except Exception:
            status = getattr(resp, 'status_code', None)

        if status == 415:
            # Retry with text if we used json first; otherwise retry with json
            logger.warning("Send-verification returned 415; retrying with alternate content-type")
            if json_body is not None and not tried_text:
                tried_text = True
                text_body = json_body.get('email') if isinstance(json_body, dict) else str(json_body)
                resp = _post_text(text_body)
            elif text_body is not None and not tried_json:
                tried_json = True
                json_body = {"email": text_body}
                resp = _post_json(json_body)

        # Log response body for debugging mail delivery issues
        try:
            resp_text = resp.text
            logger.debug("Send-verification response body: %s", resp_text)
        except Exception:
            resp_text = None
            logger.debug("Send-verification response body: <unavailable>")

        try:
            status = int(getattr(resp, 'status_code', None))
        except Exception:
            status = getattr(resp, 'status_code', None)

        if status == 400:
            try:
                body_json = resp.json()
                msg = body_json.get("message") or (resp_text if resp_text else "Invalid request.")
            except Exception:
                msg = resp_text or "Invalid request."
            return False, msg, False

        if status == 429:
            return False, "Too many requests; please try again later.", True

        if isinstance(status, int) and status >= 500:
            return False, resp_text or "Server error. Please try again later.", True

        if not (isinstance(status, int) and 200 <= status < 300):
            try:
                body_json = resp.json()
                msg = body_json.get("message") or (resp_text if resp_text else "Unexpected error occurred.")
            except Exception:
                msg = resp_text or "Unexpected error occurred."
            return False, msg, True

        try:
            body = resp.json()
        except ValueError:
            logger.debug("No JSON returned from send-verification endpoint; assuming success")
            # return server text when available to help debugging
            return True, (resp_text or "Verification code sent."), False

        if isinstance(body, dict) and body.get("message"):
            # If server returned additional data or timestamps, return it as a fourth value
            data = None
            # prefer explicit data dict
            if isinstance(body.get('data'), dict):
                data = body.get('data')
            # or top-level createdAt timestamp
            elif isinstance(body.get('createdAt'), str):
                data = body
            if data is not None:
                return True, body.get("message"), False, data
            return True, body.get("message"), False

        # Prefer a textual response body when present to surface helpful messages
        email_addr = payload.get('email') if isinstance(payload, dict) else None
        if email_addr:
            logger.info("Send-verification succeeded for email: %s", email_addr)
        return True, (resp_text or "Verification code sent."), False

    except requests.exceptions.Timeout:
        logger.warning("Send-verification request timed out")
        return False, "Request timed out. Please check your network and try again.", True

    except requests.exceptions.ConnectionError:
        logger.warning("Unable to connect to send-verification endpoint")
        return False, "Unable to connect to server. Please try again later.", True

    except Exception:
        logger.exception("Unexpected error during send-verification request")
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
