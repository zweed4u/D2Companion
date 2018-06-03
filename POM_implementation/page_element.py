#!/usr/bin/python3

import os
from web_driver import WebDriver
from random import choice, getrandbits
from selenium.webdriver.support.expected_conditions import visibility_of
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import staleness_of


class PageElement(object):
    def __init__(self, locator=None, element=None):
        """
        Initializes the PageElement object
        :param locator: (Optional) The page element locator
        :param element: (Optional unless locator is not set) A Selenium WebElement object
        :return: None
        """
        self.driver = WebDriver().get()
        if locator is None and element is None:
            raise Exception("Must supply either a locator, element, or both to initialize PageElement!")
        if locator is not None:
            self.locator = locator
        if element is not None:
            self._web_element = element
        else:
            self._web_element = None

    def __getattr__(self, name):
        """
        Gets attributes from the WebElement if the attribute is not present in PageElement
        :param name: The name of the attribute.
        :return: The WebElement's attribute.
        """
        return getattr(self.web_element, name)

    @property
    def web_element(self):
        if not self._web_element:
            self._web_element = self.driver.find_element(self.locator.by, self.locator.string)
        return self._web_element

    def is_enabled(self):
        """
        This is a wrapper for Selenium WebElement's is_enabled method.
        :return: True if the web element is enabled, otherwise False
        """
        return self.web_element.is_enabled()

    def is_displayed(self):
        """
        This is a wrapper for Selenium WebElement's is_displayed method.
        :return: True if the web element is displayed, otherwise False
        """
        return self.web_element.is_displayed()

    def is_clickable(self):
        """
        This method will determine if the element is clickable.
        :return: True if clickable, otherwise False
        """
        return self.is_enabled() and self.is_displayed()

    def is_selected(self):
        """
        This is a wrapper for Selenium WebElement's is_selected method.
        :return: True if the web element is selected, otherwise False
        """
        return self.web_element.is_selected()

    def get_value(self):
        """
        This is a wrapper for Selenium WebElement's get_attribute method.
        This method returns the value attribute of the web element.
        :return: The PageElement's 'value' attribute.
        """
        return self.get_attribute('value')

    def get_attribute(self, name):
        """
        This is a wrapper for Selenium WebElement's get_attribute method.
        :param name: The name of the attribute.
        :return: The PageElement's attribute.
        """
        return self.web_element.get_attribute(name)

    def scroll_to(self, timeout=30):
        """
        This methods scrolls the element into view.
        This method adds the functionality for scrolling elements into view before executing the click.
        :param timeout: How long the wait should last until it times out.
        :return: None
        """
        self.driver.execute_script('arguments[0].scrollIntoView(false)', self.web_element)
        WebDriverWait(self.driver, timeout).until(visibility_of(self.web_element))

    def click(self, scroll_to=True):
        """
        This is a wrapper for Selenium WebElement's click method.
        This method adds the functionality for scrolling elements into view before executing the click.
        :param scroll_to: Bool determining if we should scroll to the element before clicking or not.
        :return: None
        """
        if scroll_to:
            self.scroll_to()
        self.web_element.click()

    def click_random_chance(self, scroll_to=True):
        """
        This is method will "flip a coin" to decide whether to click the element or not.
        This method adds the functionality for scrolling elements into view before executing the click.
        :param scroll_to: Bool determining if we should scroll to the element before clicking or not.
        :return: None
        """
        if not getrandbits(1):
            self.click(scroll_to=scroll_to)

    def send_keys(self, *value):
        """
        This is a wrapper for Selenium WebElement's send_keys method.
        This method adds the functionality for scrolling elements into view before executing
        :return: None
        """
        self.scroll_to()
        self.web_element.send_keys(*value)

    def send_enter(self):
        """
        This is a wrapper for Selenium WebElement's send_keys method to send the enter key.
        This method adds the functionality for scrolling elements into view before executing
        :return: None
        """
        self.scroll_to()
        self.web_element.send_keys(Keys.ENTER)

    def clear(self):
        """
        This is a wrapper for Selenium WebElement's clear method.
        This method adds the functionality for scrolling elements into view before executing
        :return: None
        """
        self.scroll_to()
        self.web_element.clear()

    def select_by_index(self, index):
        """
        This is a wrapper for Selenium WebElement's select_by_index method.
        This method adds the functionality for scrolling elements into view before executing
        :return: None
        """
        self.scroll_to()
        Select(self.web_element).select_by_index(index)

    def select_by_value(self, value):
        """
        This is a wrapper for Selenium WebElement's select_by_value method.
        This method adds the functionality for scrolling elements into view before executing
        :return: None
        """
        self.scroll_to()
        Select(self.web_element).select_by_value(value)

    def select_by_text(self, text):
        """
        This is a wrapper for Selenium WebElement's select_by_value method.
        This method adds the functionality for scrolling elements into view before executing
        :return: None
        """
        self.scroll_to()
        Select(self.web_element).select_by_visible_text(text)

    def first_selected_option(self):
        """
        This is a wrapper for Selenium WebElement's first_selected_option method.
        This method adds the functionality for scrolling elements into view before executing
        :return: The first selected (or currently selected for regular select lists) option in the select list
        """
        self.scroll_to()
        return str(Select(self.web_element).first_selected_option)

    def first_selected_option_value(self):
        """
        This will return the value of the first selected (or currently selected) option in a select list.
        This method adds the functionality for scrolling elements into view before executing
        :return: The value of the first selected (or currently selected for regular select lists) option in the select list
        """
        self.scroll_to()
        return str(Select(self.web_element).first_selected_option.get_attribute("value"))

    def all_selected_options(self):
        """
        This is a wrapper for Selenium WebElement's all_selected_options method.
        This method adds the functionality for scrolling elements into view before executing
        :return: A list of all of the selected options in the select list
        """
        self.scroll_to()
        return Select(self.web_element).all_selected_options

    def all_selected_options_values(self):
        """
        This will return all the values of the selected options in a select list.
        This method adds the functionality for scrolling elements into view before executing
        :return: A list of the values of the selected options in the select list
        """
        self.scroll_to()
        return str(Select(self.web_element).first_selected_option.get_attribute("value"))

    def options(self):
        """
        This is a wrapper for Selenium WebElement's all_selected_options method.
        This method adds the functionality for scrolling elements into view before executing
        :return: A list of all of the options in the select list
        """
        self.scroll_to()
        return Select(self.web_element).options

    def options_values(self):
        """
        This will return a list of all of the values each option in a select element.
        This method adds the functionality for scrolling elements into view before executing
        :return: A list of all of the option values in the select list.
        """
        self.scroll_to()
        values = []
        for option in Select(self.web_element).options:
            values.append(str(option.get_attribute("value")))
        return values

    def select_any_random_select_option(self):
        """
        Chooses a random select option that may or may not be already selected
        and selects that option in a given select list web element.
        :return: The selected option value
        """
        random_choice = choice(self.options_values())
        self.select_by_value(random_choice)
        return random_choice

    def select_new_random_select_option(self):
        """
        Chooses a random select option that is not already selected
        and selects that option in a given select list web element.
        :return: The newly selected option value
        """
        new_choice = self.first_selected_option_value()
        timeout = 0
        # Choose a new option that is not currently selected
        while new_choice == self.first_selected_option_value():
            if timeout > 999:
                raise TimeoutError("New random select option selection timed out!\n Are you sure there is more than one option available?")
            new_choice = choice(self.options_values())
        self.select_by_value(new_choice)
        return new_choice

    def is_stale(self, element_reference):
        """
        This is a wrapper for Selenium WebElement's staleness_of expected condition.
        Note: This method was made to use with selenium WebDriverWait.until method.
        :param element_reference: The reference to the element we are checking for staleness of
        :return: True if the element is stale.
                 False otherwise
        """
        return staleness_of(element_reference)

    def wait_stale(self):
        """
        Will wait until this element becomes stale.
        :return: None
        """
        element_reference = self.web_element
        WebDriverWait(self.driver, 30).until(self.is_stale(element_reference))


class PageElementsList(list):
    def __init__(self, locator):
        """
        Initializes the PageElementsList object
        :param locator: A Locator object
        :return: None
        """
        self.driver = WebDriver().get()
        self.locator = locator
        super(PageElementsList, self).__init__()
        elements = self.driver.find_elements(locator.by, locator.string)
        for element in elements:
            self.append(PageElement(locator=self.locator, element=element))
