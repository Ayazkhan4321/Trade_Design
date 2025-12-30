import requests
from types import SimpleNamespace

from Forgot_password import forgot_password_service as service


def _make_response(status_code=200, json_data=None, json_exc=None):
    def _json():
        if json_exc:
            raise json_exc
        return json_data

    resp = SimpleNamespace()
    resp.status_code = status_code
    resp.json = _json
    return resp


def _unpack(res):
    if isinstance(res, tuple) and len(res) == 3:
        return res[0], res[1]
    return res[0], res[1]


def test_invalid_email():
    res = service.send_reset_link("not-an-email")
    ok, msg = _unpack(res)
    assert ok is False
    assert "valid email" in msg.lower()


def test_success(monkeypatch):
    def fake_post(self, url, json, timeout, verify):
        return _make_response(200, {"message": "Reset link sent"})

    monkeypatch.setattr(requests.Session, "post", fake_post)

    res = service.send_reset_link("a@b.com")
    ok, msg = _unpack(res)
    assert ok is True
    assert "reset link" in msg.lower()


def test_not_found(monkeypatch):
    def fake_post(self, url, json, timeout, verify):
        return _make_response(404, {"message": "Not found"})

    monkeypatch.setattr(requests.Session, "post", fake_post)

    res = service.send_reset_link("notfound@b.com")
    ok, msg = _unpack(res)
    assert ok is False
    # Use a clear message that indicates the email is not registered
    assert "not registered" in msg.lower()


def test_timeout(monkeypatch):
    def fake_post(self, url, json, timeout, verify):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    res = service.send_reset_link("a@b.com")
    ok, msg = _unpack(res)
    assert ok is False
    assert "timed out" in msg.lower()
