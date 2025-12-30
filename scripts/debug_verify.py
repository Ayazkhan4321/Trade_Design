from Create_Account import create_account_service as svc

class DummyResp:
    def __init__(self, status_code=200, json_data=None, text='OK'):
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

print('---- verify_otp success case ----')
resp = DummyResp(status_code=200, json_data={'message':'Verified'})
svc._get_session = lambda: DummySession(resp)
print('verify_otp ->', svc.verify_otp('john@example.com','123456'))

print('\n---- verify_otp bad code case ----')
resp = DummyResp(status_code=400, json_data={'message':'Invalid code'})
svc._get_session = lambda: DummySession(resp)
print('verify_otp ->', svc.verify_otp('john@example.com','0000'))

print('\n---- send_verification server error ----')
resp = DummyResp(status_code=500, json_data={'message':'Error'})
svc._get_session = lambda: DummySession(resp)
print('send_verification ->', svc.send_verification({'email':'john@example.com'}))
