import abc

import PyWeb.utils as utils
    
class Hidden(object):
    __metaclass__ = utils.NoInstance

class Show(object):
    __metaclass__ = utils.NoInstance
    
class ReplaceWithChildren(object):
    __metaclass__ = utils.NoInstance

class Info(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getTitle(self):
        return "Unknown title"

    @abc.abstractmethod
    def getDisplay(self):
        return Show

    @abc.abstractmethod
    def getRepresentative(self):
        return None

    @abc.abstractmethod
    def __iter__(self):
        return iter([])
