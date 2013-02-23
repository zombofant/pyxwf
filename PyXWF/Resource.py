# File name: Resource.py
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
from __future__ import unicode_literals, print_function

import abc

from PyXWF.utils import ET, threading
import PyXWF.utils as utils
import PyXWF.Errors as Errors
import PyXWF.Cache as Cache


class Resource(Cache.Cachable):
    """
    Resources represent data which was loaded and can be reloaded from an
    original source. Resource derivates must implement :attr:`LastModified`
    and :meth:`update` to allow for precise caching and on-demand reload.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        super(Resource, self).__init__(**kwargs)
        self._updatelock = threading.Lock()

    @abc.abstractproperty
    def LastModified(self):
        """
        Return a :class:`datetime.datetime` object referring to the timestamp
        of last modification of the resource stored in this object (not the one
        represented by this object).

        It MUST refer to the date of last modification of the source at the time
        it was loaded or the timestamp of modification by any program code,
        which is not neccessarily the same as the current timestamp of last
        modification of the original source.
        """

    @abc.abstractmethod
    def update(self):
        """
        Check for modifications of the resource represented by this object and
        reload the data if neccessary. Should also update the value returned
        by LastModified.
        """

    def threadsafe_update(self):
        """
        The :class:`Resource` class provides basic means to make your update
        thread safe: The :meth:`update` method will only be called with the
        :attr:`_updatelock` held, if you don't overwrite this method.

        Note that this method will only be called by the framework itself; If
        you call :meth:`update` on your own, you will not be safeguarded.
        """
        with self._updatelock:
            self.update()


class XMLTree(Resource):
    """
    Represent a file-backed XML tree resource. Load the XML tree from *filename*
    and watch out for modifications.
    """

    def __init__(self, filename, **kwargs):
        super(XMLTree, self).__init__(**kwargs)
        self._tree = None
        self._filename = filename
        self._last_modified = utils.file_last_modified(filename)
        self._parse()

    def _parse(self):
        self._tree = ET.parse(self._filename)

    def LastModified(self):
        return self._last_modified

    def update(self):
        file_modified = utils.file_last_modified(self._filename)
        if file_modified is None:
            raise Errors.ResourceLost(self._filename)
        if file_modified > self._last_modified:
            self._parse()
            self._last_modified = file_modified

    @property
    def Tree(self):
        return self._tree


class XMLFileCache(Cache.FileSourcedCache):
    def _load(self, path, **kwargs):
        return XMLTree(path, **kwargs)


