from __future__ import unicode_literals

import unittest

from PyXWF.utils import ET
import PyXWF.Registry as Registry
import PyXWF.Tweaks as Tweaks

import tests.Mocks as Mocks

class DummySitleton(Tweaks.TweakSitleton):
    __metaclass__ = Registry.SitletonMeta

    def __init__(self, site):
        super(DummySitleton, self).__init__(site,
            tweak_ns=str(Mocks.MockNS),
            tweak_hooks=[
                ("tweakA", self.tweakA),
                ("tweakB", self.tweakB),
            ]
        )
        self.tweak_nodes = []

    def tweakA(self, node):
        self.tweak_nodes.append(node)

    def tweakB(self, node):
        self.tweak_nodes.append(node)


class TweakPropagation(Mocks.DynamicSiteTest):
    def setUpSitemap(self, etree, meta, plugins, tweaks, tree, crumbs):
        super(TweakPropagation, self).setUpSitemap(etree, meta, plugins, tweaks, tree, crumbs)
        self.tweak_nodes = []
        for i in xrange(10):
            tag = Mocks.MockNS.tweakA if i % 2 == 0 else Mocks.MockNS.tweakB
            node = ET.SubElement(tweaks, tag, attrib={
                "id": str(i)
            })
            self.tweak_nodes.append(node)

    def get_dummy_sitleton(self):
        self.setup_site(self.get_sitemap(self.setUpSitemap))
        return DummySitleton.at_site(self.site)

    def test_sitleton(self):
        self.assertIsNotNone(self.get_dummy_sitleton())

    def test_tweaks(self):
        sitleton = self.get_dummy_sitleton()
        for sitleton_node, ref_node in zip(sitleton.tweak_nodes, self.tweak_nodes):
            self.assertEqual(sitleton_node.tag, ref_node.tag)
            self.assertEqual(sitleton_node.attrib, ref_node.attrib)

    def tearDown(self):
        del self.tweak_nodes
        super(TweakPropagation, self).tearDown()

