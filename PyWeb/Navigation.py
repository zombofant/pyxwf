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

def getDisplayAttr(node, name, default=Show):
    v = node.get(name)
    if v is None:
        return default
    else:
        try:
            return {
                "show": Show,
                "hide": Hidden,
                "hidden": Hidden,
                "replace-with-children": ReplaceWithChildren
            }[v]
        except KeyError:
            raise ValueError("Invalid {0} attribute on {1}: {2}".format(name, utils.splitTag(node)[1], v))
