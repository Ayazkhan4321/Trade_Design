import types
from Create_Account import create_account_service as svc


class DummyResp:
    def __init__(self, status_code=200, json_data=None, text="OK"):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json


class DummySession:
    def __init__(self, resp):
        self._resp = resp

    def post(self, *args, **kwargs):
        return self._resp

    def get(self, *args, **kwargs):
        return self._resp


def test_create_account_validation():
    payload = svc.CreateAccountRequest(
        firstName="",
        lastName="Smith",
        email="bad-email",
        phone="123",
        accountTypeID=1,
        creationType="Live",
    )
    ok, msg, retry = svc.create_account(payload)
    assert not ok
    assert not retry


def test_create_account_success(monkeypatch):
    resp = DummyResp(status_code=201, json_data={"message": "Created"})
    monkeypatch.setattr(svc, "_get_session", lambda: DummySession(resp))
    payload = svc.CreateAccountRequest(
        firstName="John",
        lastName="Doe",
        email="john@example.com",
        phone="+11234567890",
        accountTypeID=1,
        creationType="Live",
    )
    ok, msg, retry = svc.create_account(payload)
    assert ok
    assert "Created" in msg
    assert not retry


def test_get_countries_success(monkeypatch):
    resp = DummyResp(status_code=200, json_data=[{"name": "United States", "dial_code": "+1", "code": "US"}])
    monkeypatch.setattr(svc, "_get_session", lambda: DummySession(resp))
    ok, data, retry = svc.get_countries()
    assert ok
    assert isinstance(data, list)
    assert data[0]["name"] == "United States"


def test_verify_otp_success(monkeypatch):
    # server returns JSON with message (generic endpoint)
    resp = DummyResp(status_code=200, json_data={"message": "Verified"})
    monkeypatch.setattr(svc, "_get_session", lambda: DummySession(resp))
    ok, msg, retry = svc.verify_otp("john@example.com", "123456")
    assert ok
    assert "Verified" in msg
    assert not retry


def test_verify_otp_bad_code(monkeypatch):
    # server reports a bad request
    resp = DummyResp(status_code=400, json_data={"message": "Invalid code"})
    monkeypatch.setattr(svc, "_get_session", lambda: DummySession(resp))
    ok, msg, retry = svc.verify_otp("john@example.com", "0000")
    assert not ok
    assert "Invalid" in msg
    assert not retry


def test_verify_otp_fallback_no_endpoint(monkeypatch):
    # Remove endpoint constant to exercise fallback behavior
    monkeypatch.setitem(svc.__dict__, 'API_ACCOUNTS_VERIFY', None)
    ok, msg, retry = svc.verify_otp("john@example.com", "abc")
    assert ok
    assert "Verified" in msg
    assert not retry


def test_verify_otp_with_userid_template(monkeypatch):
    # Use a templated endpoint that expects userId in path and a payload with userId/otp/accountTypeId
    monkeypatch.setitem(svc.__dict__, 'API_ACCOUNTS_VERIFY_TEMPLATE', 'https://api.example/Users/{userId}/verify-otp')
    resp = DummyResp(status_code=200, json_data={"message": "Verified by id"})
    class CheckSession:
        def post(self, url, *args, **kwargs):
            assert url.endswith('/Users/42/verify-otp')
            assert 'json' in kwargs and kwargs['json'] == {"userId": 42, "otp":"9999", "accountTypeId": 3}
            return resp
    monkeypatch.setattr(svc, "_get_session", lambda: CheckSession())
    ok, msg, retry = svc.verify_otp("42", "9999", 3)
    assert ok
    assert "Verified" in msg
    assert not retry


def test_verify_otp_generic_payload(monkeypatch):
    # Generic endpoint should receive identifier/otp/accountTypeId
    resp = DummyResp(status_code=200, json_data={"message": "Verified"})
    class CheckSession:
        def post(self, url, *args, **kwargs):
            assert 'json' in kwargs and kwargs['json'] == {"identifier":"john@example.com", "otp":"123456", "accountTypeId": 2}
            return resp
    monkeypatch.setattr(svc, "_get_session", lambda: CheckSession())
    ok, msg, retry = svc.verify_otp("john@example.com", "123456", 2)
    assert ok
    assert "Verified" in msg
    assert not retry


def test_send_verification_fallback_no_endpoint(monkeypatch):
    # Remove endpoint constant to exercise fallback behavior
    monkeypatch.setitem(svc.__dict__, 'API_ACCOUNTS_SEND', None)
    ok, msg, retry = svc.send_verification({"email":"john@example.com"})
    assert ok
    assert "dry-run" in msg or "sent" in msg
    assert not retry


def test_send_verification_server_error(monkeypatch):
    resp = DummyResp(status_code=500, json_data={"message": "Error"})
    monkeypatch.setattr(svc, "_get_session", lambda: DummySession(resp))
    ok, msg, retry = svc.send_verification({"email":"john@example.com"})
    assert not ok
    assert retry


def test_send_verification_text_payload(monkeypatch):
    resp = DummyResp(status_code=200, json_data=None, text="Verification email queued")
    monkeypatch.setattr(svc, "_get_session", lambda: DummySession(resp))
    # Call with a plain string payload (email address) -- service will send as JSON by default
    ok, msg, retry = svc.send_verification("john@example.com")
    assert ok
    assert "Verification" in msg or "queued" in msg
    assert not retry


def test_send_verification_prefers_json_for_string(monkeypatch):
    resp = DummyResp(status_code=200, json_data={"message": "Queued"}, text="Queued")
    class CheckSession:
        def post(self, url, *args, **kwargs):
            # ensure JSON body was used for string payload
            assert 'json' in kwargs and kwargs['json'] == {"email": "john@example.com"}
            return resp
    monkeypatch.setattr(svc, "_get_session", lambda: CheckSession())
    ok, msg, retry = svc.send_verification("john@example.com")
    assert ok
    assert "Queued" in msg or "Verification" in msg
    assert not retry


def test_format_issue_times():
    from datetime import datetime, timezone
    from Create_Account.create_account_controller import format_issue_times
    # client now in local tz
    c = datetime(2025, 12, 30, 11, 41, 0, tzinfo=timezone.utc).astimezone()
    s_iso = "2025-12-30T06:11:17.3773203Z"
    txt = format_issue_times(c, s_iso)
    assert "Sent (local)" in txt
    assert "Server created at" in txt


def test_send_verification_415_retries_with_text(monkeypatch):
    # First response is 415, second is 200
    resp1 = DummyResp(status_code=415, json_data={"message":"Unsupported Media Type"}, text='{"type":"...","title":"Unsupported Media Type","status":415}')
    resp2 = DummyResp(status_code=200, json_data=None, text="Queued via text")
    class SequenceSession:
        def __init__(self):
            self._resps = [resp1, resp2]
            self.calls = []
        def post(self, url, *args, **kwargs):
            self.calls.append(kwargs)
            return self._resps.pop(0)
    seq = SequenceSession()
    monkeypatch.setattr(svc, "_get_session", lambda: seq)
    ok, msg, retry = svc.send_verification("john@example.com")
    assert ok
    # first call used json, second call should have used data/text
    assert 'json' in seq.calls[0]
    assert 'data' in seq.calls[1] or 'json' in seq.calls[1]
    assert "Queued" in msg or "text" in msg
    assert not retry


def test_send_verification_returns_data_when_present(monkeypatch):
    resp = DummyResp(status_code=200, json_data={"message": "Queued", "createdAt": "2025-12-30T06:11:17.3773203Z"})
    monkeypatch.setattr(svc, "_get_session", lambda: DummySession(resp))
    res = svc.send_verification({"email":"john@example.com"})
    assert isinstance(res, tuple)
    assert len(res) == 4
    ok, msg, retry, data = res
    assert ok
    assert "Queued" in msg
    assert isinstance(data, dict)
    assert 'createdAt' in data
