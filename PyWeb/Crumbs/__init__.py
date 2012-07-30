import abc

class CrumbBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, site, node):
        super(CrumbBase, self).__init__()
        self.site = site
        self.ID = node.get("id")

    @abc.abstractmethod
    def render(self, ctx):
        pass
