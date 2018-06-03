#!/usr/bin/python3


class Locator:
    def __init__(self, by, string):
        """
        This class represents a locator for a web page element
        :param by: Locator type
        :param string: locator string
        """
        self.by = by
        self.string = string

    @property
    def tuple(self):
        """
        Create a tuple representation of the locator.
        :return: A tuple of the by and string locator properties.
        """
        return self.by, self.string
