from __future__ import unicode_literals, print_function

import abc

import PyWeb.Cache as Cache

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

