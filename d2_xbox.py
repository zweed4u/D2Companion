#!/usr/bin/python3
import os
import time
import urllib
import requests
from bs4 import BeautifulSoup
from selenium import webdriver


class LoginLive:
    def __init__(self):
        self.api_key = <API_KEY_HERE>
        self.state = None
        self.code = None
        self.base_headers = {
            'Host':               'www.bungie.net',
            'X-API-Key':          self.api_key,
            'Accept':             '*/*',
            'User-Agent':         'bungie_mobile/201805160404.2445 CFNetwork/808.2.16 Darwin/16.3.0',
            'Accept-Language':    'en-us',
            'Accept-Encoding':    'gzip, deflate',
            'Connection':         'keep-alive'
        }
        self.session = requests.session()

    def _get_landing_page(self):
        params = {
            'head': False,
            'lc': 'en'
        }
        self.session.request('GET', 'https://www.bungie.net/platform/Content/GetContentByTagAndType/front-page-items/ContentSet/en/', params=params, headers=self.base_headers)
        params = {
            'includestreaming': True,
            'lc':               'en'
        }
        self.session.request('GET', 'https://www.bungie.net/platform/GlobalAlerts/', params=params, headers=self.base_headers)
        self.session.request('GET', 'https://www.bungie.net/platform/Content/Site/Featured/', params={'lc':'en'}, headers=self.base_headers)

    def login(self, username, password, use_requests=False):
        self._get_landing_page()
        if use_requests:
            data = {
                'bungiemobiletkr':        <MOBILE_TOKEN_HERE>,  # Figure out if this is device specific/static or if we need to scrape/parse for it
                'bungiemobileapptype':    'BnetMobile',
                'bungiemobiledevicename': None  # 'null'
            }
            login_headers = {
                'Host':             'www.bungie.net',
                'Origin':           None,  #'null'
                'Content-Type':     'application/x-www-form-urlencoded',
                'Connection':       'keep-alive',
                'X-API-Key':        self.api_key,
                'Accept':           'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'User-Agent':       'Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Mobile/14C92',
                'Accept-Language':  'en-us',
                'Accept-Encoding':  'gzip, deflate'
            }
            self.session.request('POST', 'https://www.bungie.net/Mobi/en/User/SignIn/Xuid', data=data, headers=login_headers)
            redirect_headers = {
                'Host':              'www.bungie.net',
                'Accept':            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'X-API-Key':         self.api_key,
                'Proxy-Connection':  'keep-alive',
                'User-Agent':        'Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Mobile/14C92',
                'Accept-Language':   'en-us',
                'Accept-Encoding':   'gzip, deflate',
                'Connection':        'keep-alive'
            }

            # Bungie -> login.live microsoft
            init_login = self.session.request('GET', 'http://www.bungie.net/en/User/SignIn/Xuid', params={'flowStart':'1'}, headers=redirect_headers)
            ### PARSE STATE FROM HERE
            state = init_login.content.decode('utf8').split('state=')[1].split('&')[0]
            contextid = init_login.content.decode('utf8').split('&contextid=')[1].split('&')[0]
            bk = init_login.content.decode('utf8').split('bk=')[1].split('&')[0]
            uaid = init_login.content.decode('utf8').split('uaid=')[1].split('&')[0]
            client_id = init_login.content.decode('utf8').split('client_id=')[1].split('&')[0]
            pid = init_login.content.decode('utf8').split('pid=')[1].split('\'')[0]
            id = init_login.content.decode('utf8').split('&id=')[1].split('\'')[0]
            cobrandid = init_login.content.decode('utf8').split('cobrandid=')[1].split('&')[0]
            soup = BeautifulSoup(init_login.content.decode('utf8'), 'html5lib')
            js = soup.findAll('script')
            """
            print(state)
            print(contextid)
            print(bk)
            print(uaid)
            print(client_id)
            print(pid)
            print(id)
            print(cobrandid)
            """
            for script in js:
                if 'name="PPFT"' in str(script):
                    soup = BeautifulSoup(str(script).split('sFTTag:\'')[1].split('\',')[0], 'html5lib')
                    flowtoken = str(soup.findAll('input', {'name': 'PPFT'})[0]['value'])
            #print(flowtoken)
            headers = {
                'Host':               'login.live.com',
                'Accept':             'application/json',
                'hpgact':             '0',
                'Accept-Language':    'en-us',
                'hpgid':              '38',  # Figure out if this is static
                'Accept-Encoding':    'gzip, deflate',
                'Content-Type':       'application/json; charset=UTF-8',
                'Origin':             'https://login.live.com',
                'client-request-id':  uaid,
                'User-Agent':         'Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Mobile/14C92',
                'Connection':         'keep-alive'
            }
            json = {
                "checkPhones": False,
                "flowToken": flowtoken,
                "isCookieBannerShown": False,
                "isFidoSupported": False,
                "isOtherIdpSupported": False,
                "isRemoteNGCSupported": True,
                "uaid": uaid,
                "username": username
            }
            params = {
                'client_id':<client_id>,  # Figure out if this is static
                'scope':'Xboxlive.signin Xboxlive.offline_access',
                'response_type':'code',
                'redirect_uri':'https://www.bungie.net/en/User/SignIn/Xuid',
                'display':'touch',
                'locale':'en',
                'state':state,
                'vv':'1600',  # Figure out if this is static
                'mkt':'EN-US',
                'lc':'1033'  # Figure out if this is static
            }
            params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            self.session.request('POST', 'https://login.live.com/GetCredentialType.srf', params=params, json=json, headers=headers)
            data = {
                'i13':               '0',  # Figure out if this is static
                'login':             username,
                'loginfmt':          username,
                'type':              '11',  # Figure out if this is static
                'LoginOptions':      '3',  # Figure out if this is static
                'lrt':               '',  # Figure out if this is static
                'lrtPartition':      '',  # Figure out if this is static
                'hisRegion':         '',  # Figure out if this is static
                'hisScaleUnit':      '',  # Figure out if this is static
                'passwd':            password,
                'ps':                '2',  # Figure out if this is static
                'psRNGCDefaultType': '',  # Figure out if this is static
                'psRNGCEntropy':     '',  # Figure out if this is static
                'psRNGCSLK':         '',  # Figure out if this is static
                'canary':            '',  # Figure out if this is static
                'ctx':               '',  # Figure out if this is static
                'hpgrequestid':      '',  # Figure out if this is static
                'PPFT':              flowtoken,
                'PPSX':              'Passp',  # Figure out if this is static ('P')
                'NewUser':           '1',  # Figure out if this is static
                'FoundMSAs':         '',  # Figure out if this is static
                'fspost':            '0',  # Figure out if this is static
                'i21':               '0',  # Figure out if this is static
                'CookieDisclosure':  '0',  # Figure out if this is static
                'IsFidoSupported':   '0',  # Figure out if this is static
                'i2':                '36',  # Figure out if this is static
                'i17':               '0',  # Figure out if this is static
                'i18':               '__ConvergedLoginPaginatedStrings|1,__ConvergedLogin_PCore|1,',  # Figure out if this is static
                'i19':               '19768'  # Figure out if this is static !!
            }

            params = {
                'client_id':<client_id>,  # Figure out if this is static
                'scope':'Xboxlive.signin Xboxlive.offline_access',  # Figure out if this is static
                'response_type':'code',  # Figure out if this is static
                'redirect_uri':'https://www.bungie.net/en/User/SignIn/Xuid',  # Figure out if this is static
                'display':'touch',  # Figure out if this is static
                'locale':'en',  # Figure out if this is static
                'state':state,
                'contextid':contextid,
                'bk':bk,
                'uaid':uaid,
                'pid':pid
            }
            params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            headers = {
                'Host':             'login.live.com',
                'Content-Type':     'application/x-www-form-urlencoded',
                'Origin':           'https://login.live.com',
                'Connection':       'keep-alive',
                'Accept':           'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'User-Agent':       'Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Mobile/14C92',
                'Accept-Language':  'en-us',
                'Accept-Encoding':  'gzip, deflate'
            }

            login_response = self.session.request('POST', 'https://login.live.com/ppsecure/post.srf', params=params, data=data, headers=headers)

        else:
            driver = webdriver.Chrome(f'{os.getcwd()}/chromedriver')
            driver.get('http://www.bungie.net/en/User/SignIn/Xuid')

            username_field = driver.find_element_by_name('loginfmt')
            username_field.send_keys(username)

            next_button = driver.find_element_by_id('idSIButton9')
            next_button.click()

            time.sleep(1)

            password_field = driver.find_element_by_name('passwd')
            password_field.send_keys(password)

            sign_in_button = driver.find_element_by_id('idSIButton9')
            sign_in_button.click()
            code = driver.current_url.split('code=')[1].split('&')[0]
            state = driver.current_url.split('state=')[1]
            self.state = state
            self.code = code
            cookies = driver.get_cookies()
            driver.close()

        headers = {
            'Host':             'www.bungie.net',
            'Accept':           '*/*',
            'X-API-Key':        self.api_key,
            'X-csrf':           self.state,
            'Accept-Language':  'en-us',
            'User-Agent':       'bungie_mobile/201805160404.2445 CFNetwork/808.2.16 Darwin/16.3.0',
            'Accept-Encoding':  'gzip, deflate',
            'Connection':       'keep-alive'

        }
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])
        return self.session
