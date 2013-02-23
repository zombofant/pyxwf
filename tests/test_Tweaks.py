# File name: test_Tweaks.py
# This file is part of: pyxwf
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyxwf please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
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

