#!/usr/bin/python3

import os
import configparser
from xbox_live import XboxLive

root_directory = os.getcwd()
c = configparser.ConfigParser()
configFilePath = os.path.join(root_directory, 'config.cfg')
c.read(configFilePath)

t = XboxLive(c.get('authentication', 'username_email'), c.get('authentication', 'password'))
t.go()
t.sign_in()