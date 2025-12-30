import logging
import os
from typing import Optional, Tuple

import requests
from pydantic import BaseModel, ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from api.config import API_AUTH_LOGIN, API_BASE_URL, API_VERIFY_TLS, API_TIMEOUT, API_RETRIES
from pathlib import Path

# Module logger
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Helper to determine a per-user session directory. Use APPDATA (Windows),
# XDG_DATA_HOME (Linux), or user home directory fallback. We compute it on
# every call so tests that modify env vars work as expected.

def _session_dir() -> Path:
    p = Path(os.getenv("APPDATA") or os.getenv("XDG_DATA_HOME") or Path.home()) / ".my_design"
    p.mkdir(parents=True, exist_ok=True)
    return p


class AuthData(BaseModel):
    token: Optional[str] = None
    accessToken: Optional[str] = None


class AuthResponse(BaseModel):
    data: AuthData
    message: Optional[str] = None


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


def authenticate(account_type: str, email: str, password: str) -> Tuple[bool, str]:
    """Authenticate with the API.

    Returns (success: bool, message: str).
    """
    url = API_AUTH_LOGIN

    payload = {"email": email, "password": password}

    session = _get_session()

    try:
        logger.debug("Hitting API: %s", url)
        response = session.post(url, json=payload, timeout=API_TIMEOUT, verify=API_VERIFY_TLS)

        logger.debug("Status Code: %s", response.status_code)

        # ---- HTTP-level errors ----
        if response.status_code == 401:
            return False, "Invalid email or password."

        if response.status_code == 400:
            return False, "Invalid request. Please check inputs."

        if response.status_code >= 500:
            return False, "Server error. Please try again later."

        if response.status_code != 200:
            return False, "Unexpected error occurred."

        # ---- Parse & validate response ----
        try:
            payload_json = response.json()
        except ValueError:
            logger.exception("Failed to parse JSON from auth response")
            return False, "Invalid server response."

        try:
            validated = AuthResponse.parse_obj(payload_json)
        except ValidationError:
            logger.exception("Response schema validation failed")
            return False, "Invalid server response structure."

        token = validated.data.token or validated.data.accessToken
        if token:
            _store_token(token, email)
            return True, validated.message or "Login successful"
        else:
            return False, validated.message or "Login failed."

    except requests.exceptions.Timeout:
        logger.warning("Auth request timed out")
        return False, "Request timed out. Check your internet."

    except requests.exceptions.ConnectionError:
        logger.warning("Unable to connect to auth server")
        return False, "Unable to connect to server."

    except Exception:
        logger.exception("Unexpected error during authentication")
        return False, "Unexpected error occurred."


def _store_token(token: str, username: str = "user") -> None:
    """Store token securely when possible (try keyring, otherwise fallback to file).

    Also write a small `session.user` file with the username so the
    application can show who is currently signed in. This keeps the
    token storage compatible with existing tests which expect a
    `session.token` file when `keyring` is unavailable.
    """
    # Try to import keyring explicitly and handle it not being installed
    try:
        import keyring  # type: ignore
    except ModuleNotFoundError:
        logger.info("`keyring` package not installed; falling back to file storage")
    else:
        try:
            service = "my_design_app"  # change as appropriate
            keyring.set_password(service, username, token)
            logger.debug("Token stored in keyring for user %s", username)

            # Also persist the username locally so UI can look it up later
            try:
                with open("session.user", "w", encoding="utf-8") as uf:
                    uf.write(username)
                logger.debug("Username written to session.user")
            except Exception:
                logger.exception("Failed to write session.user after keyring storage")

            return
        except Exception:
            logger.exception("Failed to store token in keyring; falling back to file storage")

    # Fallback: write to file with restrictive permissions in SESSION_DIR
    token_path = _session_dir() / "session.token"
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        # mode 0o600 -> owner read/write only (POSIX). On Windows permissions differ.
        with os.fdopen(os.open(str(token_path), flags, 0o600), "w") as f:
            f.write(token)
        logger.debug("Token written to %s with restricted permissions", token_path)
    except Exception:
        logger.exception("Failed to store token to file")

    # Store username for UI purposes (separate file)
    try:
        user_path = _session_dir() / "session.user"
        with user_path.open("w", encoding="utf-8") as uf:
            uf.write(username)
        logger.debug("Username written to %s", user_path)
    except Exception:
        logger.exception("Failed to write session.user file")



def _migrate_legacy_file(filename: str) -> None:
    """If a legacy session file exists in cwd, move it into the per-user SESSION_DIR.

    This provides backward compatibility for older versions that wrote files
    to the application CWD instead of the per-user data directory.
    """
    legacy = Path.cwd() / filename
    dest = _session_dir() / filename
    try:
        if legacy.exists() and not dest.exists():
            # Read then write then remove to avoid cross-device rename issues
            with legacy.open("r", encoding="utf-8") as src:
                data = src.read()
            with dest.open("w", encoding="utf-8") as dst:
                dst.write(data)
            try:
                legacy.unlink()
            except Exception:
                logger.exception("Failed to remove legacy session file %s", legacy)
            logger.debug("Migrated legacy session file %s to %s", legacy, dest)
    except Exception:
        logger.exception("Failed to migrate legacy session file %s", filename)


def get_token() -> Optional[str]:
    """Return the currently stored token or None if not found."""
    # Try keyring first if username is known
    try:
        import keyring  # type: ignore
    except ModuleNotFoundError:
        keyring = None

    username = get_current_user()
    if keyring and username:
        try:
            service = "my_design_app"
            token = keyring.get_password(service, username)
            if token:
                return token
        except Exception:
            logger.exception("Failed to read token from keyring")

    # Migrate any legacy files left in CWD (for backward compatibility)
    _migrate_legacy_file("session.token")

    # Fallback: read token file from SESSION_DIR
    token_path = _session_dir() / "session.token"
    try:
        if token_path.exists():
            with token_path.open("r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        logger.exception("Failed to read token from file")
    return None


def get_current_user() -> Optional[str]:
    """Return the stored username/email if available.

    Also migrate legacy `session.user` from CWD if present.
    """
    # Migrate legacy file if present in CWD
    _migrate_legacy_file("session.user")

    user_path = _session_dir() / "session.user"
    try:
        if user_path.exists():
            with user_path.open("r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        logger.exception("Failed to read session.user")
    return None


def clear_token() -> None:
    """Remove stored token and username from keyring/file storage."""
    # Try keyring removal if possible and username is known
    try:
        import keyring  # type: ignore
    except ModuleNotFoundError:
        keyring = None

    username = get_current_user()
    if keyring and username:
        try:
            service = "my_design_app"
            keyring.delete_password(service, username)
            logger.debug("Deleted keyring token for user %s", username)
        except Exception:
            logger.exception("Failed to delete token from keyring")

    # Remove token/user files from SESSION_DIR if they exist
    for p in (_session_dir() / "session.token", _session_dir() / "session.user"):
        try:
            if p.exists():
                p.unlink()
                logger.debug("Removed %s", p)
        except Exception:
            logger.exception("Failed to remove %s", p)

