import os
import requests
import json


class A3RT(object):

    def __init__(self):
        self.key = os.getenv('A3RT_TALK_API_KEY', 'DZZA0sAvLkc31eR5KyAMrGTUsU9jPXgg')
        self.url = 'https://api.a3rt.recruit-tech.co.jp/talk/v1/smalltalk'

    def talk(self, talking):
        r = requests.post(self.url, {'apikey': self.key, 'query': talking}, timeout=3)
        data = json.loads(r.text)
        if data['status'] == 0:
            t = data['results']
            ret = t[0]['reply']
        else:
            ret = ''
        return ret
