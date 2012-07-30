import abc

class CrumbBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, site, tag, node):
        super(CrumbBase, self).__init__()
        self.site = site

    @abc.abstractmethod
    def render(self, mainNode):
        pass
