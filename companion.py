#!/usr/bin/python3
import json
import requests
from d2_xbox import LoginLive

class D2Companion:
    def __init__(self):
        self.session = None
        self.base_url = 'https://www.bungie.net'

    def _make_request(self, method, endpoint, params=None, data=None, json=None, headers=None, ret_json=True):
        if ret_json:
            return self.session.request(method, f'{self.base_url}/{endpoint}', params=params, data=data, json=json, headers=headers).json()
        else:
            return self.session.request(method, f'{self.base_url}/{endpoint}', params=params, data=data, json=json, headers=headers)


    def login(self, username, password):
        self.my_login = LoginLive()
        self.session = self.my_login.login(username, password)

    def get_basics(self):
        headers = {
            'Host':             'www.bungie.net',
            'Accept':           '*/*',
            'X-API-Key':        self.my_login.api_key,
            'X-csrf':           self.my_login.state,
            'Accept-Language':  'en-us',
            'User-Agent':       'bungie_mobile/201805160404.2445 CFNetwork/808.2.16 Darwin/16.3.0',
            'Accept-Encoding':  'gzip, deflate',
            'Connection':       'keep-alive'

        }
        print(self._make_request('GET', 'platform/User/GetBungieNetUser/', params={'lc':'en'}, headers=headers))


D2 = D2Companion()
D2.login(<username_here>, <password_here>)
D2.get_basics()
