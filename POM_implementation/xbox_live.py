#!/usr/bin/python3
import os
import time
import urllib
import requests
import configparser
from bs4 import BeautifulSoup
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from page import Page
from locator import Locator
from page_element import PageElement

class XboxLive(Page):
    def __init__(self, username_email, password):
        super(XboxLive, self).__init__('https://login.live.com')
        self.login_username = username_email  # email, phone, skype
        self.login_password = password
        self.base_url = 'https://login.live.com'

    def go(self):
        if self.base_url not in self.driver.current_url:
            self.driver.get('http://www.bungie.net/en/User/SignIn/Xuid')
            if not self.is_here():
                raise Exception("Go took the user to the wrong page. "
                                "\n Current Page: " + self.driver.current_url +
                                "\n Expected Page: " + self.base_url)

    def is_here(self):
        attempts = 10
        while attempts > 0:
            # Check if the current url is the correct url
            if self.base_url.lower() in self.driver.current_url.lower():
                # If it is, return True
                return True
            # If not, sleep for 1 second and try again
            else:
                time.sleep(1)
            # Decrement the attempts count by one
            attempts -= 1
        return False

    @property
    def username_field(self):
        """
        The username text field on the login page
        :return: A Selenium WebElement representing the username text field
        """
        return PageElement(Locator(By.NAME, "loginfmt"))

    @property
    def next_button(self):
        """
        The username text field on the login page
        :return: A Selenium WebElement representing the username text field
        """
        return PageElement(Locator(By.ID, "idSIButton9"))

    @property
    def password_field(self):
        """
        The username text field on the login page
        :return: A Selenium WebElement representing the username text field
        """
        return PageElement(Locator(By.NAME, "passwd"))

    @property
    def sign_in_button(self):
        """
        The username text field on the login page
        :return: A Selenium WebElement representing the username text field
        """
        return PageElement(Locator(By.ID, "idSIButton9"))

    @property
    def keep_me_signed_in_radio_button(self):
        """
        The username text field on the login page
        :return: A Selenium WebElement representing the username text field
        """
        return PageElement(Locator(By.NAME, "KMSI"))

    def sign_in(self):
        # Clear the username field. Enter the username.
        self.username_field.clear()
        self.username_field.send_keys(self.login_username)
        self.username_field.send_keys(Keys.ENTER)
        time.sleep(1)
        # Clear the password field. Enter the password.
        self.password_field.clear()
        self.password_field.send_keys(self.login_password)
        # Click the login button.
        self.password_field.send_keys(Keys.ENTER)
