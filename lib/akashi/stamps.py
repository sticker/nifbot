import json
import ast
import urllib.request
from lib import get_logger


class Stamps(object):

    def __init__(self):
        self.url = 'https://atnd.ak4.jp/api/cooperation/NIFTYCorporation/stamps'
        self.logger = get_logger(__name__)

    def api_request(self, post_data):
        headers = {
            'Content-Type': 'application/json',
        }
        req = urllib.request.Request(self.url, json.dumps(post_data).encode(), headers)
        with urllib.request.urlopen(req) as res:
            body = json.loads(res.read().decode('utf8'))
            return body

    def begin(self, token):
        post_data = {
            'token': token,
            'type': 11
        }
        return self.api_request(post_data)

    def finish(self, token):
        post_data = {
            'token': token,
            'type': 12
        }
        return self.api_request(post_data)
