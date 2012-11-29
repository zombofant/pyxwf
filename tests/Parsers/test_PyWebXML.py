from __future__ import unicode_literals

import unittest

from PyXWF.utils import ET
import PyXWF.Namespaces as NS
import PyXWF.ContentTypes as ContentTypes

import tests.Mocks as Mocks

class PyWebXML(Mocks.DynamicSiteTest):
    def _parse(self, tree):
        parser = self.site.parser_registry[ContentTypes.PyWebXML]
        return parser.parse_tree(tree)

    def setUp(self):
        super(PyWebXML, self).setUp()
        self.setup_site(self.get_sitemap(self.setUpSitemap))

    def test_preserve_html(self):
        script = NS.XHTML("script", href="foo")
        test_tree = NS.PyWebXML("page",
            NS.PyWebXML("meta",
                NS.PyWebXML("title", "fnord"),
                script
            ),
            NS.XHTML("body")
        )

        parsed = self._parse(test_tree)

        self.maxDiff = None
        self.assertMultiLineEqual(
            ET.tostring(parsed.to_PyWebXML_page()),
            ET.tostring(test_tree)
        )
