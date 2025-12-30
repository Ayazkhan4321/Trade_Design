from Create_Account import create_account_service as svc
import traceback
import inspect

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

resp = DummyResp(status_code=200, json_data={'message':'Verified'})
svc._get_session = lambda: DummySession(resp)
try:
    r = svc.verify_otp('john@example.com','123456')
    print('verify_otp returned:', r)
except Exception as e:
    print('verify_otp raised exception:')
    traceback.print_exc()

# Also check source
print('\nFunction source:\n')
print(inspect.getsource(svc.verify_otp))
