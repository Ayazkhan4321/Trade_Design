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

resp = DummyResp(status_code=400, json_data={'message':'Invalid code'})
s = DummySession(resp)
resp2 = s.post(None)
print('resp2.status_code type:', type(getattr(resp2,'status_code',None)), 'value:', getattr(resp2,'status_code',None))
try:
    status = int(getattr(resp2,'status_code',None))
except Exception as e:
    status = getattr(resp2,'status_code',None)
print('computed status type:', type(status), 'value:', status)
print('resp2.json():', resp2.json())
