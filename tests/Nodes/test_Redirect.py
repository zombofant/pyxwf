from __future__ import unicode_literals

import unittest

from PyXWF.utils import ET
import PyXWF.Errors as Errors

import PyXWF.Nodes.Redirect as Redirect

import tests.Mocks as Mocks

class RedirectInternal(Mocks.DynamicSiteTest):
    def setUpSitemap(self, etree, meta, plugins, tweaks, tree, crumbs,
            method="found", cachable=True):
        internal = ET.SubElement(tree, Redirect.RedirectNS.internal, attrib={
            "method": method,
            "to": "bar",
            "cachable": str(cachable)
        })
        bar = ET.SubElement(tree, Redirect.RedirectNS.internal, attrib={
            "id": "bar",
            "name": "bar"
        })

    def get_redirect(self, method, cachable=True):
        self.setup_site(self.get_sitemap(self.setUpSitemap, method=method, cachable=cachable))
        redirect = self.site.tree.index
        self.ctx = Mocks.MockedContext.from_site(self.site)
        return redirect

    def test_internal(self):
        redirect = self.get_redirect("internal")
        self.assertRaises(Errors.InternalRedirect, redirect.resolve_path, self.ctx, "")

    def test_found(self):
        redirect = self.get_redirect("found")
        self.assertRaises(Errors.HTTP.Found, redirect.redirect, self.ctx)
        self.assertSequenceEqual(["private"], list(self.ctx.CacheControl))

    def test_permanent(self):
        redirect = self.get_redirect("moved-permanently")
        self.assertRaises(Errors.HTTP.MovedPermanently, redirect.redirect, self.ctx)
        self.assertSequenceEqual(["private"], list(self.ctx.CacheControl))

    def test_temporary(self):
        redirect = self.get_redirect("temporary-redirect", False)
        self.assertRaises(Errors.HTTP.TemporaryRedirect, redirect.redirect, self.ctx)
        self.assertSequenceEqual([], list(self.ctx.CacheControl))

    def test_see_other(self):
        redirect = self.get_redirect("see-other")
        self.assertRaises(Errors.HTTP.SeeOther, redirect.redirect, self.ctx)
        self.assertSequenceEqual(["private"], list(self.ctx.CacheControl))

