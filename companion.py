#!/usr/bin/python3
import os
import json
import shutil
import sqlite3
import zipfile
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
        self.character_hashes = {
            'character_1': None,  # personal: warlock
            'character_2': None,  # personal: titan
            'character_3': None  # personal: hunter
        }
        self.hash_to_item = {}
        self.owned_item_hash_instance_id = {
            'character_1': {},
            'character_2': {},
            'character_3': {}
        }
        self.config = config
        self.base_url = 'https://www.bungie.net'

    def _make_request(self, method, endpoint, params=None, data=None, json=None, headers=None, ret_json=True):
        if ret_json:
            return self.session.request(method, f'{self.base_url}/{endpoint}', params=params, data=data, json=json, headers=headers).json()
        else:
            return self.session.request(method, f'{self.base_url}/{endpoint}', params=params, data=data, json=json, headers=headers)

    def fetch_all_from_db_query(self, sql_query, db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(sql_query)
        return c.fetchall()

    def populate_item_hash_dict(self, use_plumbling=False):
        if use_plumbling:
            all_item_definitions = requests.request('GET', 'https://destiny.plumbing/en/raw/DestinyInventoryItemDefinition.json').json()
            for item_hash in all_item_definitions.keys():
                self.hash_to_item[int(item_hash)] = all_item_definitions[item_hash]['displayProperties']['name']
        else:
            world_content_db_path = f"http://bungie.net{self.get_manifest()['Response']['mobileWorldContentPaths']['en']}"
            local_filename = world_content_db_path.split('/')[-1]
            # TODO add db file exist?
            r = requests.request('GET', world_content_db_path, stream=True)
            with open(local_filename, 'wb') as file:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            zip_ref = zipfile.ZipFile(f'{os.getcwd()}/{local_filename}', 'r')
            zip_ref.extractall(f'{os.getcwd()}/{local_filename.split(".")[0]}')
            zip_ref.close()
            shutil.copy(f'{os.getcwd()}/{local_filename.split(".")[0]}/{local_filename}', os.getcwd())
            shutil.rmtree(f'{os.getcwd()}/{local_filename.split(".")[0]}')
            shutil.move(f'{os.getcwd()}/{local_filename}', f'{os.getcwd()}/{local_filename}.sqlite3')
            db_file_path = f'{os.getcwd()}/{local_filename}.sqlite3'

            id_json_items_list_tuple = self.fetch_all_from_db_query('SELECT id, json from DestinyInventoryItemDefinition', db_file_path)

            for item_tuple in id_json_items_list_tuple:
                item_hash = item_tuple[0]
                item_json = json.loads(item_tuple[1])
                self.hash_to_item[int(item_hash) & 0xFFFFFFFF] = item_json['displayProperties']['name']
            return self.hash_to_item   

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
        self.populate_item_hash_dict()

    def get_basics(self):
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
        payload = {
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
        return self._make_request('POST', 'platform/Content/SearchEx/en/', params=query_string, json=payload, headers=post_headers)

    def get_update_state_app_info(self):
        post_headers = self.headers
        post_headers.update({'Content-Type':'application/x-www-form-urlencoded'})
        payload = {
            "ApnLocale": "en",
            "ApnToken": str(self.config.get('app_info', 'app_token')),
            "AppInstallationId": str(self.config.get('app_info', 'app_id')),
            "AppType": "BnetMobile",
            "DeviceType": 5,
            "MembershipType": 254
        }
        return self._make_request('POST', 'platform/User/UpdateStateInfoForMobileAppPair/', params={'lc':'en'}, json=payload, headers=post_headers)

    def get_groups(self):
        if self.group_id is None:
            self.get_group_messages()
        return self._make_request('GET', f'platform/GroupV2/{self.group_id}/', params={'lc':'en'}, headers=self.headers)

    def convert_item_hash(self):
        # TODO implement match of inventory to hash_to_item dictionary
        pass

    def get_triumphs(self):
        return self._make_request('GET', f'platform/Destiny2/1/Triumphs/{self.membership_id}/', params={'lc':'en'}, headers=self.headers)

    def get_profile(self, hardcoded_class_hash=False, use_plumbling=False):
        if self.membership_id is None:
            self.get_memberships_by_id()
        query_string = {
            'components':'100,101,102,103,200,201,202,203,204,205,500,300,301,302,303,304,305,306,307,308,400,401,402',
            'lc':'en'
        }
        profile_response = self._make_request('GET', f'platform/Destiny2/1/Profile/{self.membership_id}/', params=query_string, headers=self.headers)
        character_dictionary = profile_response['Response']['characters']['data']

        if hardcoded_class_hash:
            titan_class_hash = 3655393761
            hunter_class_hash = 671679327
            warlock_class_hash = 2271682572
        else:
            if use_plumbling:
                class_hash_lookup_dict = requests.request('GET', 'https://destiny.plumbing/en/raw/DestinyClassDefinition.json').json()
                for listed_class_hash in class_hash_lookup_dict:
                    if class_hash_lookup_dict[listed_class_hash]['displayProperties']['name'].lower() == 'titan':
                        titan_class_hash = class_hash_lookup_dict[listed_class_hash]['hash']
                    elif class_hash_lookup_dict[listed_class_hash]['displayProperties']['name'].lower() == 'warlock':
                        warlock_class_hash = class_hash_lookup_dict[listed_class_hash]['hash']
                    elif class_hash_lookup_dict[listed_class_hash]['displayProperties']['name'].lower() == 'hunter':
                        hunter_class_hash = class_hash_lookup_dict[listed_class_hash]['hash']
            else:
                world_content_db_path = f"http://bungie.net{self.get_manifest()['Response']['mobileWorldContentPaths']['en']}"
                local_filename = world_content_db_path.split('/')[-1]
                # TODO add db file exist?
                r = requests.request('GET', world_content_db_path, stream=True)
                with open(local_filename, 'wb') as file:
                    for chunk in r.iter_content(chunk_size=1024): 
                        if chunk:
                            file.write(chunk)
                zip_ref = zipfile.ZipFile(f'{os.getcwd()}/{local_filename}', 'r')
                zip_ref.extractall(f'{os.getcwd()}/{local_filename.split(".")[0]}')
                zip_ref.close()
                shutil.copy(f'{os.getcwd()}/{local_filename.split(".")[0]}/{local_filename}', os.getcwd())
                shutil.rmtree(f'{os.getcwd()}/{local_filename.split(".")[0]}')
                shutil.move(f'{os.getcwd()}/{local_filename}', f'{os.getcwd()}/{local_filename}.sqlite3')
                db_file_path = f'{os.getcwd()}/{local_filename}.sqlite3'
                class_list_jsons = [json.loads(class_json[0]) for class_json in self.fetch_all_from_db_query('SELECT json from DestinyClassDefinition', db_file_path)]
                for d2_class in class_list_jsons:
                    if d2_class['displayProperties']['name'].lower() == 'warlock':
                        warlock_class_hash = d2_class['hash']
                    elif d2_class['displayProperties']['name'].lower() == 'titan':
                        titan_class_hash = d2_class['hash']
                    elif d2_class['displayProperties']['name'].lower() == 'hunter':
                        hunter_class_hash = d2_class['hash']

        for character in character_dictionary:
            if int(character_dictionary[character]['classHash']) == warlock_class_hash:
                self.character_hashes.update({'character_1':character_dictionary[character]['characterId']})

            elif int(character_dictionary[character]['classHash']) == hunter_class_hash:
                self.character_hashes.update({'character_3':character_dictionary[character]['characterId']})

            elif int(character_dictionary[character]['classHash']) == titan_class_hash:
                self.character_hashes.update({'character_2':character_dictionary[character]['characterId']})
            else:
                raise Exception('Class Hash wasn\'t found!')

        # Handle equipped equipment
        character_equipment = profile_response['Response']['characterEquipment']['data']
        for character_id in list(character_equipment.keys()):
            for item in character_equipment[character_id]['items']:
                self.owned_item_hash_instance_id[list(self.character_hashes.keys())[list(self.character_hashes.values()).index(character_id)]].update({item['itemHash']:item['itemInstanceId']})

        # Handle unequipped equipment (inventory)
        character_inventory = profile_response['Response']['characterInventories']['data']
        for character_id in list(character_inventory.keys()):
            for item in character_inventory[character_id]['items']:
                try:
                    self.owned_item_hash_instance_id[list(self.character_hashes.keys())[list(self.character_hashes.values()).index(character_id)]].update({item['itemHash']:item['itemInstanceId']})
                except:
                    pass

        # TODO collect vaulted items in own dictionary
        return profile_response

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

    def create_fireteam(self, fireteam_title, is_public, has_mic, players_needed, players_already_in_fireteam, character):
        # TODO - add dictionary traversal and LUTs for activities, platform and character hash
        # character - from your hashes self.character_hashes.values()
        # anything  5
        # crucible  2
        # nightfall 4
        # raid      1
        # trials    3
        # psn 1
        # xbx 2
        # blz 3
        payload = {
            "activityType": 4,  # from above comment/s (nightfall)
            "alternateSlotCount": players_already_in_fireteam,
            "isPublic": is_public,
            "locale": "en",
            "ownerCharacterId": list(self.character_hashes.values())[0],  # this is my titan hash - using first one has example
            "ownerHasMicrophone": has_mic,
            "platform": 2,  # from above comment/s (xbox)
            "playerSlotCount": players_needed,
            "title": fireteam_title
        }
        return self._make_request('POST', 'platform/Fireteam/Clan/0/Create/', params={'lc':'en'}, json=payload, headers=self.headers)

    def get_my_fireteam(self, fireteam_id):
        # fireteam_id can be retrieved self.create_fireteam() response
        return self._make_request('GET', f'platform/Fireteam/Clan/0/Summary/{fireteam_id}/', payload={'lc':'en'}, headers=self.headers)

    def invite_fireteam_to_game(self, fireteam_id):
        # fireteam_id can be retrieved self.create_fireteam() response
        return self._make_request('POST', f'platform/Fireteam/Clan/0/Invite/{fireteam_id}/0/', payload={'lc':'en'}, headers=self.headers)

    def close_fireteam(self, fireteam_id):
        # fireteam_id can be retrieved self.create_fireteam() response
        return self._make_request('POST', f'platform/Fireteam/Clan/0/Close/{fireteam_id}/', payload={'lc':'en'}, headers=self.headers)

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
        # Implement parameterization - just grab first class in the character hash dict
        query_string = {
            'mode':  '0',
            'count': '25',
            'page':  '0',
            'lc':    'en'
        }
        return self._make_request('GET', f'platform/Destiny2/1/Account/{self.membership_id}/Character/{list(self.character_hashes.values())[0]}/Stats/Activities/', params=query_string, headers=self.headers)

    # titan   *944
    # warlock *945
    # hunter  *946
    def equip_item(self, character_hash, item_instance_id):
        payload = {
            "characterId":str(character_hash),
            "itemId":str(item_instance_id),
            "membershipType":1
        }
        return self._make_request('POST', 'platform/Destiny2/Actions/Items/EquipItem/', params={'lc':'en'}, json=payload, headers=self.headers)

    def transfer_item_to_vault(self, from_character_hash, item_instance_id, item_hash):
        payload = {
            "stackSize":1,
            "itemId":str(item_instance_id),
            "transferToVault":True,
            "membershipType":1,
            "itemReferenceHash":int(item_hash),
            "characterId":str(from_character_hash)
        }
        return self._make_request('POST', 'platform/Destiny2/Actions/Items/TransferItem/', params={'lc':'en'}, json=payload, headers=self.headers)

    def transfer_item_from_vault(self, to_character_hash, item_instance_id, item_hash):
        payload = {
            "stackSize":1,
            "itemId":str(item_instance_id),
            "transferToVault":False,
            "membershipType":1,
            "itemReferenceHash":int(item_hash),
            "characterId":str(to_character_hash)
        }
        return self._make_request('POST', 'platform/Destiny2/Actions/Items/TransferItem/', params={'lc':'en'}, json=payload, headers=self.headers)

    def transfer_from_character_3_to_character_1(self, item_instance_id, item_hash):
        if None in [character_hash for character_class, character_hash in self.character_hashes.items()]:
            self.get_profile()
        self.transfer_item_to_vault(self.character_hashes['character_3'], item_instance_id, item_hash)
        self.transfer_item_from_vault(self.character_hashes['character_1'], item_instance_id, item_hash)

    def transfer_from_character_3_to_character_2(self, item_instance_id, item_hash):
        if None in [character_hash for character_class, character_hash in self.character_hashes.items()]:
            self.get_profile()
        self.transfer_item_to_vault(self.character_hashes['character_3'], item_instance_id, item_hash)
        self.transfer_item_from_vault(self.character_hashes['character_2'], item_instance_id, item_hash)

    def transfer_from_character_2_to_character_1(self, item_instance_id, item_hash):
        if None in [character_hash for character_class, character_hash in self.character_hashes.items()]:
            self.get_profile()
        self.transfer_item_to_vault(self.character_hashes['character_2'], item_instance_id, item_hash)
        self.transfer_item_from_vault(self.character_hashes['character_1'], item_instance_id, item_hash)

    def transfer_from_character_2_to_character_3(self, item_instance_id, item_hash):
        if None in [character_hash for character_class, character_hash in self.character_hashes.items()]:
            self.get_profile()
        self.transfer_item_to_vault(self.character_hashes['character_2'], item_instance_id, item_hash)
        self.transfer_item_from_vault(self.character_hashes['character_3'], item_instance_id, item_hash)

    def transfer_from_character_1_to_character_3(self, item_instance_id, item_hash):
        if None in [character_hash for character_class, character_hash in self.character_hashes.items()]:
            self.get_profile()
        self.transfer_item_to_vault(self.character_hashes['character_1'], item_instance_id, item_hash)
        self.transfer_item_from_vault(self.character_hashes['character_3'], item_instance_id, item_hash)

    def transfer_from_character_1_to_character_2(self, item_instance_id, item_hash):
        if None in [character_hash for character_class, character_hash in self.character_hashes.items()]:
            self.get_profile()
        self.transfer_item_to_vault(self.character_hashes['character_1'], item_instance_id, item_hash)
        self.transfer_item_from_vault(self.character_hashes['character_2'], item_instance_id, item_hash)

    def exploit_add_kill_tracker(self, character_hash, item_id, is_crucible=False):
        data = {
            "affectedItemId": str(item_id),
            "characterId": str(character_hash),
            "membershipType": 1,
            "type": 1
        }
        correlation_id = self.session.request('POST', 'https://www.bungie.net/platform/Destiny2/Awa/Initialize/', params={'lc':'en'}, headers=self.headers).json()['Response']['correlationId']
        action_token = self.session.request('GET', f'https://www.bungie.net/platform/Destiny2/Awa/GetActionToken/{correlation_id}/', params={'lc':'en'}, headers=self.headers).json()['Response']['actionToken']

        """ even needed? only action token in payload for socket
        # TODO flesh this method out - "Secret nonce received via the PUSH notification" ???
        nonce = self._get_nonce()
        payload = {
            "correlationId": correlation_id,
            "nonce": nonce,
            "selection": 2
        }
        self.session.request('POST', f'https://www.bungie.net/platform/Destiny2/Awa/AwaProvideAuthorizationResult/', params={'lc':'en'}, data=payload, headers=self.headers).json()
        """
        crucible_tracker_hash = 38912240
        kill_tracker_hash = 2302094943
        payload = {
            "actionToken": action_token,
            "characterId": str(character_hash),
            "itemInstanceId": str(item_id),
            "membershipType": 1,
            "plug": {
                "plugItemHash": crucible_tracker_hash if is_crucible else kill_tracker_hash,
                "socketIndex": 9
            }
        }
        response = self.session.request('POST', 'https://www.bungie.net/platform/Destiny2/Actions/Items/InsertSocketPlug/', params={'lc':'en'}, data=payload, headers=self.headers).json()
        # Catch "DestinyShardRelayProxyTimeout"
        if response['ErrorCode'] != 1 or response['ErrorStatus'] != 'Success':
            print(response['ErrorStatus'])
            print(response['Message'])
        else:
            print(response)


root_directory = os.getcwd()
c = configparser.ConfigParser()
configFilePath = os.path.join(root_directory, 'config.cfg')
c.read(configFilePath)

D2 = D2Companion(c)
D2.login(c.get('authentication', 'username_email'), c.get('authentication', 'password'))
if PRETTY_PRINT:
    #print(json.dumps(D2.get_profile(), indent=4))
    pass
else:
    #print(D2.get_profile())
    pass
D2.get_profile()
#print(json.dumps(D2.hash_to_item, indent=4))
#print(json.dumps(D2.get_my_character(), indent=4))
print(json.dumps(D2.owned_item_hash_instance_id, indent=4))
