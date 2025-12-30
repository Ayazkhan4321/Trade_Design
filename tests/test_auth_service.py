import types
import requests
from types import SimpleNamespace

import auth.auth_service as auth_service


def _make_response(status_code=200, json_data=None, json_exc=None):
    def _json():
        if json_exc:
            raise json_exc
        return json_data

    resp = SimpleNamespace()
    resp.status_code = status_code
    resp.json = _json
    return resp


def test_auth_success(monkeypatch, tmp_path):
    # prevent actual token writes
    monkeypatch.setattr(auth_service, "_store_token", lambda token, username=None: None)

    def fake_post(self, url, json, timeout, verify):
        return _make_response(200, {"data": {"token": "abc"}, "message": "ok"})

    monkeypatch.setattr(requests.Session, "post", fake_post)

    ok, msg = auth_service.authenticate("user", "a@b.com", "pw")
    assert ok is True
    assert "ok" in msg


def test_auth_invalid_json(monkeypatch):
    monkeypatch.setattr(auth_service, "_store_token", lambda token, username=None: None)

    def fake_post(self, url, json, timeout, verify):
        return _make_response(200, json_exc=ValueError("Bad JSON"))

    monkeypatch.setattr(requests.Session, "post", fake_post)

    ok, msg = auth_service.authenticate("user", "a@b.com", "pw")
    assert ok is False
    assert "Invalid server response" in msg


def test_auth_401(monkeypatch):
    def fake_post(self, url, json, timeout, verify):
        return _make_response(401, {"message": "Unauthorized"})

    monkeypatch.setattr(requests.Session, "post", fake_post)

    ok, msg = auth_service.authenticate("user", "a@b.com", "pw")
    assert ok is False
    assert "Invalid email or password" in msg


def test_auth_timeout(monkeypatch):
    def fake_post(self, url, json, timeout, verify):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    ok, msg = auth_service.authenticate("user", "a@b.com", "pw")
    assert ok is False
    assert "timed out" in msg.lower()


def test_store_token_fallback_no_keyring(monkeypatch, tmp_path):
    # Ensure we operate in a temp dir by making the app data dir point at tmp
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    # Make importing keyring raise ModuleNotFoundError
    import builtins
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "keyring":
            raise ModuleNotFoundError("No module named 'keyring'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    # Call _store_token and expect fallback to file in SESSION_DIR
    auth_service._store_token("mytoken", username="u")

    p = tmp_path / ".my_design" / "session.token"
    assert p.exists()
    assert p.read_text() == "mytoken"

    # And username should be persisted (used for UI display)
    q = tmp_path / ".my_design" / "session.user"
    assert q.exists()
    assert q.read_text() == "u"
