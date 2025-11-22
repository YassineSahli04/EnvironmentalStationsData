from requests.auth import AuthBase

from Crypto.Hash import HMAC
from Crypto.Hash import SHA256
from datetime import datetime

class AuthHmacMetos(AuthBase):
    def __init__(self, apiRoute, publicKey, privateKey, method):
        self._publicKey = publicKey
        self._privateKey = privateKey
        self._method = method
        self._apiRoute = apiRoute

    def __call__(self, request):
        dateStamp = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        request.headers['Request-Date'] = dateStamp
        msg = (self._method + self._apiRoute + dateStamp + self._publicKey).encode(encoding='utf-8')
        h = HMAC.new(self._privateKey.encode(encoding='utf-8'), msg, SHA256)
        signature = h.hexdigest()
        request.headers['Authorization'] = 'hmac ' + self._publicKey + ':' + signature
        return request