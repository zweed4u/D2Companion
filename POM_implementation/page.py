#!/usr/bin/python3

import time

from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.wait import WebDriverWait

from web_driver import WebDriver


class Page(object):
    def __init__(self, base_url):
        self.base_url = base_url
        self.url = self.base_url
        self.redirect_url = None
        self.driver = WebDriver().get()

    def go(self):
        """
        Causes the webdriver to go to the url of this page object and check that we made it there.
        :exception: Raised if we are on the wrong page.
        :return: None
        """
        self.driver.get(self.url)
        if not self.is_here():
            raise Exception("Go took the user to the wrong page. "
                            "\n Current Page: " + self.driver.current_url +
                            "\n Expected Page: " + self.url)

    def is_here(self):
        """
        Checks if we are at this page by checking that
        the current webpage has the same url as this page object's url.
        :return: True if we are at this page.
                 False if we are not at this page.
        """
        attempts = 10
        while attempts > 0:
            # Check if the current url is the correct url
            curr_url = self.driver.current_url.lower()
            if self.url.lower() in curr_url:
                # If it is, return True
                return True
            # Some pages have redirect to a different url, check that url next
            elif self.redirect_url is not None and curr_url == self.redirect_url.lower():
                return True
            # If not, sleep for 1 second and try again
            else:
                time.sleep(1)
            # Decrement the attempts count by one
            attempts -= 1
        return False

    def refresh(self):
        """
        Refreshes the page via the web driver and waits until the refresh finishes.
        :return: None
        """
        old_page_html_element = self.driver.find_element_by_tag_name('html')
        self.driver.refresh()
        WebDriverWait(self.driver, 30).until(staleness_of(old_page_html_element))

    def wait_for_refresh(self, timeout=30):
        """
        Waits until this page was refreshed by waiting until the page html web element is stale.
        Can be used as a generator to run with other functions.
        :param timeout: How long the wait should last until it times out.
        :return: None
        """
        old_page_html_element = self.driver.find_element_by_tag_name('html')
        yield
        WebDriverWait(self.driver, timeout).until(staleness_of(old_page_html_element))
