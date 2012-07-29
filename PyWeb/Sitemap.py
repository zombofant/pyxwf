from __future__ import unicode_literals

import xml.etree.ElementTree as ET

import PyWeb.utils as utils
from PyWeb.Registry import NodePlugins

class Site(object):
    namespace = "http://pyweb.sotecware.net/site"
    
    def __init__(self, sitemapFileLike=None, **kwargs):
        super(Site, self).__init__(**kwargs)
        if sitemapFileLike is not None:
            try:
                self.loadSitemap(ET.parse(sitemapFileLike).getroot())
            except:
                self.clear()
                raise
        else:
            self.clear()

    def _require(self, value, name):
        if value is None:
            raise ValueError("Sitemap requires a valid {0} tag.".format(name))

    def _loadMeta(self, root):
        meta = root.find("{{{0}}}meta".format(self.namespace))
        if meta is None:
            raise ValueError("meta tag must be present.")
        self.title = unicode(meta.findtext("{{{0}}}title".format(self.namespace)))
        license = meta.find("{{{0}}}license".format(self.namespace))
        if license is not None:
            self.licenseName = unicode(license.text)
            self.licenseHref = unicode(license.get("href", None))

        self.root = unicode(meta.findtext("{{{0}}}root".format(self.namespace)))
        self.urlRoot = unicode(meta.findtext("{{{0}}}urlRoot".format(self.namespace)))
        self._require(self.title, "title")
        self._require(self.root, "root")
        self._require(self.urlRoot, "urlRoot")

    def _loadNode(self, node):
        plugin = NodePlugins.getPluginInstance(node, self)
        children = list(map(self._loadNode, node))
        if len(children) > 0:
            plugin.extend(children)
        return plugin

    def _loadTree(self, tree):
        self.tree = []
        root = self.root
        self.tree = list(map(self._loadNode, tree))

    def loadSitemap(self, root):
        self._loadMeta(root)
        tree = root.find("{{{0}}}tree".format(self.namespace))
        self._loadTree(tree)

    def clear(self):
        self.title = None
        self.licenseName = None
        self.licenseHref = None

    def __unicode__(self):
        base = """<Site title={0!r}>""".format(self.title)
        for node in self.tree:
            for line in node.nodeTree():
                base += "\n    "+line
        return base

