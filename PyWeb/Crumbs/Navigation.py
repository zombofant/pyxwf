import PyWeb.Registry as Registry
import PyWeb.Crumbs as Crumbs

class Navigation(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta

    def __init__(self, site, tag, node):
        super(Navigation, self).__init__(site, tag, node)
