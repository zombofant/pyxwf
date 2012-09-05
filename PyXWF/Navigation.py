"""
This module handles informational classes used by navigation-related crumbs.
"""

import abc

import PyXWF.utils as utils
import PyXWF.Types as Types

class Info(object):
    """
    This is the base class for the relevant information needed to create a
    navigation entry (and possible subentries).
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_title(self):
        """
        Return the title to be used in the navigation.
        """
        return "Unknown title"

    @abc.abstractmethod
    def get_display(self):
        """
        Return one of :data:`Hidden`, :class:`ReplaceWithChildren` or
        :data:`Show` to designate how the entry shall be represented in the
        navigation.
        """
        return Show

    @abc.abstractmethod
    def get_representative(self):
        """
        Return the :class:`~PyXWF.Nodes.Node` which represents this
        navigation entry. This is not neccessarily the same as the
        :class:`~PyXWF.Nodes.Node` instance from which this entry was
        obtained (for example for Directories returning their index node or
        redirects).
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
