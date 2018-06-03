#!/usr/bin/python3

import os
import platform
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# noinspection PyCompatibility
class WebDriver(metaclass=Singleton):
    def __init__(self, browser=None, headless=False):
        """
        Initializes the WebDriver class
        :return:
        """
        self.browser = browser
        self.driver = None
        self.headless = headless

    # noinspection PyIncorrectDocstring
    def get(self, ignore_ssl=False):
        """
        Creates the Selenium Webdriver object
        :param ignore_ssl:
        :return: A Selenium Webdriver object
        """
        if self.driver:
            return self.driver

        if os.environ.get("SAUCE_USERNAME") and os.environ.get("SAUCE_ACCESS_KEY"):
            # Use Sauce Labs to run the test
            desired_capabilities = {
                "platform": "Windows 7",
                "browserName": "firefox",
                "screenResolution": "1920x1080"
            }

            # self._browser is set by pytest plugins in primus/pytest_plugins/environment.py
            # It contains a string like this: "browser_name/os_name/version"
            if self.browser:
                browser_split = self.browser.split("/")
                if len(browser_split) >= 1:
                    desired_capabilities["browserName"] = browser_split[0]
                if len(browser_split) >= 2:
                    desired_capabilities["platform"] = browser_split[1]
                if len(browser_split) == 3:
                    desired_capabilities["version"] = browser_split[2]
            if os.environ.get("SELENIUM_BROWSER"):
                desired_capabilities["browserName"] = os.environ.get("SELENIUM_BROWSER")
            if os.environ.get("SELENIUM_PLATFORM"):
                desired_capabilities["platform"] = os.environ.get("SELENIUM_PLATFORM")
            if os.environ.get("SELENIUM_VERSION"):
                desired_capabilities["version"] = os.environ.get("SELENIUM_VERSION")
            desired_capabilities[
                "name"] = self._get_job_name() if "SELENIUM_JOB_NAME" not in os.environ else os.environ.get(
                "SELENIUM_JOB_NAME")

            profile = None
            if desired_capabilities["browserName"] == "firefox" and ignore_ssl:
                desired_capabilities["version"] = "46.0"
                desired_capabilities["marionette"] = False
                profile = webdriver.FirefoxProfile()
                profile.accept_untrusted_certs = True
                profile.assume_untrusted_cert_issuer = False

            command_executor = "http://" + os.environ.get("SAUCE_USERNAME") + ":" + os.environ.get(
                "SAUCE_ACCESS_KEY") + "@ondemand.saucelabs.com:80/wd/hub"
            driver = webdriver.Remote(command_executor=command_executor, desired_capabilities=desired_capabilities,
                                      browser_profile=profile)

            if os.environ.get("SELENIUM_HOST"):
                print("\rSauceOnDemandSessionID=" + driver.session_id + " job-name=" + desired_capabilities["name"])

            driver.implicitly_wait(10)
            self.driver = driver
            return driver
        else:
            try:
                if self.headless:
                    options = webdriver.ChromeOptions()
                    options.add_argument("headless")
                    options.add_argument("disable-gpu")
                    options.add_argument("enable-automation")
                    options.add_argument("disable-extensions")
                    options.add_argument("window-size=1920,1080")
                    driver = webdriver.Chrome("chromedriver", chrome_options=options)
                else:
                    system = platform.system()
                    options = webdriver.ChromeOptions()
                    if system == "Darwin":
                        options.add_argument("start-fullscreen")
                    driver = webdriver.Chrome("chromedriver", chrome_options=options)
                    if not system == "Darwin":
                        driver.maximize_window()
            except WebDriverException:
                # Try Firefox
                profile = webdriver.FirefoxProfile()
                profile.set_preference("xpinstall.signatures.required", False)
                driver = webdriver.Firefox()
                driver.maximize_window()
            driver.implicitly_wait(10)
            self.driver = driver
            return driver

    # noinspection PyMethodMayBeStatic
    def _get_job_name(self):

        return "Automated_Test"

    def quit(self):
        if self.driver:
            self.driver.quit()
        self.driver = None
