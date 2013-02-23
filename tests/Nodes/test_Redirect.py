# File name: test_Redirect.py
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

