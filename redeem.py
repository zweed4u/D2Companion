#!/usr/bin/python3
import os
import time
import random
import configparser

from d2_xbox import LoginLive

class Redeem:
    def __init__(self, config):
        self.session = None
        self.config = config
        self.base_url = 'https://www.bungie.net'

    def _make_request(self, method, endpoint, params=None, data=None, json=None, headers=None, ret_json=True):
        if ret_json:
            return self.session.request(method, f'{self.base_url}/{endpoint}', params=params, data=data, json=json, headers=headers).json()
        else:
            return self.session.request(method, f'{self.base_url}/{endpoint}', params=params, data=data, json=json, headers=headers)

    def login(self, username, password):
        self.my_login = LoginLive()
        self.session = self.my_login.login(username, password)
        self.headers = {
            'Host':             'www.bungie.net',
            'Accept':           '*/*',
            'X-API-Key':        self.my_login.api_key,
            'X-csrf':           self.my_login.state,
            'Accept-Language':  'en-us',
            'User-Agent':       'bungie_mobile/201805160404.2445 CFNetwork/808.2.16 Darwin/16.3.0',
            'Accept-Encoding':  'gzip, deflate',
            'Connection':       'keep-alive'

        }

    def redeem(self, code):
        query_string = {
            'lc': 'en',
            'fmt': True,
            'lcin': True
        }
        print(f'Using code: {code}')
        return self._make_request('POST', 'Platform/Tokens/ClaimAndApplyToken/0/', params=query_string, json=str(code), headers=self.headers)

    def get_random_code(self):
        valid_chars = 'ACDFGHJKLMNPRTVXY34679'
        valid_code_length = 9
        return ''.join(random.choices([c for c in valid_chars],k=valid_code_length))

root_directory = os.getcwd()
c = configparser.ConfigParser()
configFilePath = os.path.join(root_directory, 'config.cfg')
c.read(configFilePath)

D2 = Redeem(c)
D2.login(c.get('authentication', 'username_email'), c.get('authentication', 'password'))

while 1:
    print(D2.redeem(D2.get_random_code()))
    print()
    time.sleep(5)
