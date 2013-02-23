# File name: Navigation.py
# This file is part of: pyxwf
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyxwf please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
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
