import requests
from types import SimpleNamespace

from Forgot_password import forgot_password_service as service
import settings.feature_flags as flags


def _make_response(status_code=200, json_data=None, json_exc=None, text=''):
    def _json():
        if json_exc:
            raise json_exc
        return json_data

    resp = SimpleNamespace()
    resp.status_code = status_code
    resp.json = _json
    resp.text = text
    resp.headers = {}
    return resp


def test_404_neutral_message(monkeypatch):
    monkeypatch.setattr(requests.Session, 'post', lambda self, url, json, timeout, verify: _make_response(404, {"message": "Not found"}))
    # previously this test expected a neutral message; now clear messages are required
    res = service.send_reset_link('a@b.com')
    ok, msg, retry = res
    assert not ok
    assert 'not registered' in msg.lower()


def test_404_explicit_message(monkeypatch):
    monkeypatch.setattr(requests.Session, 'post', lambda self, url, json, timeout, verify: _make_response(404, {"message": "Not found"}))
    monkeypatch.setattr(flags, 'ALLOW_EXPLICIT_USER_MESSAGES', True)
    res = service.send_reset_link('a@b.com')
    ok, msg, retry = res
    assert not ok
    assert 'not registered' in msg.lower()


def test_success_includes_email_when_explicit(monkeypatch):
    monkeypatch.setattr(requests.Session, 'post', lambda self, url, json, timeout, verify: _make_response(200, {"message": "ok"}))
    res = service.send_reset_link('some@b.com')
    ok, msg, retry = res
    assert ok
    assert 'reset link' in msg.lower()
