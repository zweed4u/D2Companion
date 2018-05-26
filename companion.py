#!/usr/bin/python3
import os
import json
import requests
import configparser

from d2_xbox import LoginLive

PRETTY_PRINT = True


class D2Companion:
    def __init__(self, config):
        self.session = None
        self.headers = None
        self.group_id = None
        self.unique_name = None
        self.membership_id = None
        self.character_hashes = [None, None, None]
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

    def get_basics(self):
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
        basic_info_response = self._make_request('GET', 'platform/User/GetBungieNetUser/', params={'lc':'en'}, headers=self.headers)
        self.unique_name = basic_info_response['Response']['user']['uniqueName']
        return basic_info_response

    def get_group_messages(self):
        query_string = {
            'format': '1',
            'lc': 'en'
        }
        # 1, 1
        group_message_response = self._make_request('GET', 'platform/Message/GetGroupConversationsV2/1/1/', params=query_string, headers=self.headers)
        self.group_id = group_message_response['Response']['results'][0]['detail']['ownerEntityId']
        return group_message_response

    def get_following(self):
        # 8, 1
        return self._make_request('GET', 'platform/Activity/Following/V2/8/1/', params={'lc':'en'}, headers=self.headers)

    def get_self_user_group(self):
        if self.unique_name is None:
            self.get_basics()
        # 254, 0, 1 - xbox
        return self._make_request('GET', f'platform/GroupV2/User/254/{self.unique_name}/0/1/', params={'lc':'en'}, headers=self.headers)

    def get_potential_self_user_group(self):
        if self.unique_name is None:
            self.get_basics()
        # 254, 0, 1 - xbox
        return self._make_request('GET', f'platform/GroupV2/User/Potential/254/{self.unique_name}/0/1/', params={'lc':'en'}, headers=self.headers)

    def check_group_conversation_read_state(self):
        return self._make_request('GET', 'platform/Message/CheckGroupConversationReadState/1/', params={'lc':'en'}, headers=self.headers)

    def get_memberships_by_id(self):
        if self.unique_name is None:
            self.get_basics()
        # 254 - xbox
        membership_reponse = self._make_request('GET', f'platform/User/GetMembershipsById/{self.unique_name}/254/', params={'lc':'en'}, headers=self.headers)
        self.membership_id = membership_reponse['Response']['destinyMemberships'][0]['membershipId']
        return membership_reponse

    def get_notification_events(self):
        query_string = {
            'timeout': '90',
            'lc': 'en'
        }
        return self._make_request('GET', 'platform/Notification/Events/0/1/', params=query_string, headers=self.headers)

    def get_broadcast_notifications(self):
        return self._make_request('GET', 'platform/BroadcastNotifications/', params={'lc':'en'}, headers=self.headers)

    def get_settings(self):
        return self._make_request('GET', 'platform/Settings/', params={'lc':'en'}, headers=self.headers)

    def get_message_of_the_day(self):
        post_headers = self.headers
        post_headers.update({'Content-Type':'application/x-www-form-urlencoded'})
        query_string = {
            'head':False,
            'lc':'en'
        }
        payload_field = {
            "sortBy":0,
            "contentTypes":[
                "MessageOfTheDay"
            ],
            "modifiedDate":0,
            "creationDate":0,
            "currentPage":1,
            "itemsPerPage":1,
            "tag":"platform-ios"
        }
        payload = {
            json.dumps(payload_field): ''
        }
        return self._make_request('POST', 'platform/Content/SearchEx/en/', params=query_string, data=payload, headers=post_headers)

    def get_update_state_app_info(self):
        post_headers = self.headers
        post_headers.update({'Content-Type':'application/x-www-form-urlencoded'})
        payload = {
            '{"ApnLocale":"en","AppInstallationId":"{}}","ApnToken":"{}}': '","AppType":"BnetMobile","DeviceType":5,"MembershipType":254}'.format(self.config.get('app_info', 'app_id'), self.config.get('app_info', 'app_token'))
        }
        return self._make_request('POST', 'platform/User/UpdateStateInfoForMobileAppPair/', params={'lc':'en'}, data=payload, headers=post_headers)

    def get_groups(self):
        if self.group_id is None:
            self.get_group_messages()
        return self._make_request('GET', f'platform/GroupV2/{self.group_id}/', params={'lc':'en'}, headers=self.headers)

    def get_profile(self):
        # TODO - populate character hash list here
        if self.membership_id is None:
            self.get_memberships_by_id()
        query_string = {
            'components':'100,200',  # components definition (100,101,102,103,200,201,202,203,204,205,500,300,301,302,303,304,305,306,307,308,400,401,402)
            'lc':'en'
        }
        return self._make_request('GET', f'platform/Destiny2/1/Profile/{self.membership_id}/', params=query_string, headers=self.headers)

    def get_featured(self):
        return self._make_request('GET', 'platform/Content/Site/Featured/', params={'lc':'en'}, headers=self.headers)

    def get_global_alerts(self):
        query_string = {
            'includestreaming': True,
            'lc':               'en'
        }
        return self._make_request('GET', 'platform/GlobalAlerts/', params=query_string, headers=self.headers)

    def get_manifest(self):
        return self._make_request('GET', 'platform/Destiny2/Manifest/', params={'lc':'en'}, headers=self.headers)

    def get_trending_categories(self):
        return self._make_request('GET', 'platform/Trending/Categories/LiveEvents/0/', params={'lc':'en'}, headers=self.headers)

    def get_front_page(self):
        query_string = {
            'head': False,
            'lc':   'en'
        }
        return self._make_request('GET', 'platform/Content/GetContentByTagAndType/front-page-items/ContentSet/en/', params=query_string, headers=self.headers)

    def get_idle_notification_events(self):
        query_string = {
            'timeout':'90',
            'lc':'en'
        }
        return self._make_request('GET', 'platform/Notification/Events/2/1/', params=query_string, headers=self.headers)

    def refresh_front_page(self):
        self.get_front_page()
        self.get_trending_categories()
        self.get_featured()
        self.get_global_alerts()

    def get_gear_page(self):
        self.get_memberships_by_id()
        self.get_profile()  # with all component numbers

    def get_optional_conversations(self):
        return self._make_request('GET', f'platform/GroupV2/{self.group_id}/OptionalConversations/', params={'lc':'en'}, headers=self.headers)

    def get_clan_members(self):
        query_string = {
            'memberType':  '0',  #hardcoded?
            'currentPage': '1',  #hardcoded?
            'lc':          'en'
        }
        return self._make_request('GET', f'platform/GroupV2/{self.group_id}/Members/', params=query_string, headers=self.headers)

    def get_clan_weekly_reward_state(self):
        return self._make_request('GET', f'platform/Destiny2/Clan/{self.group_id}/WeeklyRewardState', params={'lc':'en'}, headers=self.headers)

    def get_clan_active_count(self):
        return self._make_request('GET', f'platform/Fireteam/Clan/{self.group_id}/ActiveCount/', params={'lc':'en'}, headers=self.headers)

    def get_pending_clan_members(self):
        query_string = {
            'currentPage':'1',
            'lc':'en'
        }
        return self._make_request('GET', f'platform/GroupV2/{self.group_id}/Members/Pending/', params=query_string, headers=self.headers)

    def get_available_fireteams(self):
        # all activities
        # psn ../1/0/1/1/0/
        # xbx ../2/0/1/1/0/
        # blz ../3/0/1/1/0/
        # xbox anything ../2/5/1/1/0/
        # xbox crucible ../2/2/1/1/0/
        # xbox nightfall ../2/4/1/1/0/
        # xbox trials ../2/3/1/1/0/
        # xbox raid ../2/1/1/1/0/
        return self._make_request('GET', f'platform/Fireteam/Search/Available/2/0/1/1/0/', params={'lc':'en'}, headers=self.headers)

    def get_clan_fireteams(self):
        query_string = {
            'groupFilter':False,
            'lc':'en'
        }
        # psn ../1/1/0/
        # xbx ../2/1/0/
        # blz ../3/1/0/
        return self._make_request('GET', 'platform/Fireteam/Clan/0/My/2/1/0/', params=query_string, headers=self.headers)

    def search_users(self, username_queried):
        return self._make_request('GET', f'platform/User/SearchUsersPaged/{username_queried}/1/30/', params={'lc':'en'}, headers=self.headers)

    def search_destiny_players(self, username):
        return self._make_request('GET', f'platform/Destiny2/SearchDestinyPlayer/-1/{username}/', params={'lc':'en'}, headers=self.headers)

    def global_search(self, text_queried):
        query_string = {
            'searchtext':  text_queried,
            'source':      'MobileGlobal',
            'currentpage': '1',
            'ctype':       'News',
            'head':        False,
            'lc':          'en'
        }
        return self._make_request('GET', 'platform/Content/Search/en/', params=query_string, headers=self.headers)

    def global_search_help(self, text_queried):
        query_string = {
            'searchtext':  text_queried,
            'source':      'MobileGlobal',
            'currentpage': '1',
            'ctype':       'Help HelpStep',
            'head':        False,
            'lc':          'en'
        }
        return self._make_request('GET', 'platform/Content/Search/en/', params=query_string, headers=self.headers)

    def get_direct_messages(self):
        query_string = {
            'format':'1',
            'lc':'en'
        }
        return self._make_request('GET', 'platform/Message/GetConversationsV5/1/', params=query_string, headers=self.headers)

    def get_direct_group_messages(self):
        query_string = {
            'format':'1',
            'lc':'en'
        }
        return self._make_request('GET', 'platform/Message/GetGroupConversations/1/', params=query_string, headers=self.headers)

    def get_following_info(self):
        return self._make_request('GET', 'platform/Activity/Following/Users/', params={'lc':'en'}, headers=self.headers)

    def get_platform_friend_info(self):
        return self._make_request('GET', 'platform/Activity/Friends/Paged/1/1/', params={'lc':'en'}, headers=self.headers)

    def get_recent_notifications(self):
        query_string = {
            'format':'1',
            'lc':'en'
        }
        return self._make_request('GET', 'platform/Notification/GetRecent/', params=query_string, headers=self.headers)

    def get_news(self):
        query_string = {
            'currentpage':'1',
            'itemsperpage':'15',
            'lc':'en'
        }
        return self._make_request('GET', 'platform/Content/Site/News/all/en/', params=query_string, headers=self.headers)

    def get_creations(self):
        # main page/trending ../0/8/0/
        # latest ../1/8/0/
        # rating ../2/8/0/
        return self._make_request('GET', 'platform/CommunityContent/Get/0/8/0/', params={'lc':'en'}, headers=self.headers)

    def get_my_character(self):
        # Implement parameterization (class maybe?) - need to fetch character hash from .get_profile method
        query_string = {
            'mode':  '0',
            'count': '25',
            'page':  '0',
            'lc':    'en'
        }
        return self._make_request('GET', f'platform/Destiny2/1/Account/{self.membership_id}/Character/{self.character_hashes[0]}/Stats/Activities/', params=query_string, headers=self.headers)

    def equip_item(self, character_hash, item_hash):
        payload_field = {
            "characterId":str(character_hash),
            "itemId":str(item_hash),
            "membershipType":1
        }
        payload = {
            json.dumps(payload_field): ''
        }
        return self._make_request('POST', 'platform/Destiny2/Actions/Items/EquipItem/', params={'lc':'en'}, data=payload, headers=self.headers)


root_directory = os.getcwd()
c = configparser.ConfigParser()
configFilePath = os.path.join(root_directory, 'config.cfg')
c.read(configFilePath)

D2 = D2Companion(c)
D2.login(c.get('authentication', 'username_email'), c.get('authentication', 'password'))
if PRETTY_PRINT:
    print(json.dumps(D2.get_basics(), indent=4))
else:
    print(D2.get_basics())
