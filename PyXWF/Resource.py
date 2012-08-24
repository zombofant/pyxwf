from __future__ import unicode_literals, print_function

import abc

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Errors as Errors
import PyXWF.Cache as Cache

class Resource(Cache.Cachable):
    """
    Resources represent data which was loaded and can be reloaded from an
    original source. Resource derivates must implement :prop:`LastModified`
    and :meth:`update` to allow for precise caching and on-demand reload.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def LastModified(self):
        """
        Return a :cls:`datetime.datetime` object referring to the timestamp
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


class XMLTree(Resource):
    """
    Represent a file-backed XML tree resource. Load the XML tree from *fileName*
    and watch out for modifications.
    """

    def __init__(self, fileName, **kwargs):
        super(XMLTree, self).__init__(**kwargs)
        self._tree = None
        self._fileName = fileName
        self._lastModified = utils.fileLastModified(fileName)
        self._parse()

    def _parse(self):
        self._tree = ET.parse(self._fileName)

    def LastModified(self):
        return self._lastModified

    def update(self):
        fileModified = utils.fileLastModified(self._fileName)
        if fileModified is None:
            raise Errors.ResourceLost(self._fileName)
        if fileModified > self._lastModified:
            self._parse()
            self._lastModified = fileModified

    @property
    def Tree(self):
        return self._tree


class XMLFileCache(Cache.FileSourcedCache):
    def _load(self, path, **kwargs):
        return XMLTree(path, **kwargs)


