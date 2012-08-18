"""
This module handles informational classes used by navigation-related crumbs.
"""

import abc

import PyWeb.utils as utils
import PyWeb.Types as Types

class Info(object):
    """
    This is the base class for the relevant information needed to create a
    navigation entry (and possible subentries).
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getTitle(self):
        """
        Return the title to be used in the navigation.
        """
        return "Unknown title"

    @abc.abstractmethod
    def getDisplay(self):
        """
        Return one of :cls:`Hidden`, :cls:`ReplaceWithChildren` or :cls:`Show`
        to designate how the entry shall be represented in the navigation.
        """
        return Show

    @abc.abstractmethod
    def getRepresentative(self):
        """
        Return the :cls:`NodeBase` which represents this navigation entry. This
        is not neccessarily the same as the :cls:`NodeBase` instance from which
        this entry was obtained (for example for Directories returning their
        index node or redirects).
        """
        return None

class ReplaceWithChildren(object):
    """
    Special value to replace the navigation entry with its children.
    """
    __metaclass__ = utils.NoInstance

Show = 1
Hidden = 0

DisplayMode = Types.AllowBoth(Types.EnumMap(
    {
        "never-show": -1,
        "hidden": 0,
        "show": 1,
        "replace-with-children": ReplaceWithChildren
    }
), Types.Typecasts.int)
