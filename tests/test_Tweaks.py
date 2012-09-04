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
            tweakNS=str(Mocks.MockNS),
            tweakHooks=[
                ("tweakA", self.tweakA),
                ("tweakB", self.tweakB),
            ]
        )
        self.tweakNodes = []

    def tweakA(self, node):
        self.tweakNodes.append(node)

    def tweakB(self, node):
        self.tweakNodes.append(node)


class TweakPropagation(Mocks.DynamicSiteTest):
    def setUpSitemap(self, etree, meta, plugins, tweaks, tree, crumbs):
        super(TweakPropagation, self).setUpSitemap(etree, meta, plugins, tweaks, tree, crumbs)
        self.tweakNodes = []
        for i in xrange(10):
            tag = Mocks.MockNS.tweakA if i % 2 == 0 else Mocks.MockNS.tweakB
            node = ET.SubElement(tweaks, tag, attrib={
                "id": str(i)
            })
            self.tweakNodes.append(node)

    def getDummySitleton(self):
        self.setupSite(self.getSitemap(self.setUpSitemap))
        return DummySitleton.atSite(self.site)

    def test_sitleton(self):
        self.assertIsNotNone(self.getDummySitleton())

    def test_tweaks(self):
        sitleton = self.getDummySitleton()
        for sitletonNode, refNode in zip(sitleton.tweakNodes, self.tweakNodes):
            self.assertEqual(sitletonNode.tag, refNode.tag)
            self.assertEqual(sitletonNode.attrib, refNode.attrib)

    def tearDown(self):
        del self.tweakNodes
        super(TweakPropagation, self).tearDown()

