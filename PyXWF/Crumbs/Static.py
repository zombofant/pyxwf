# File name: Static.py
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
import copy

from PyXWF.utils import ET, _F
import PyXWF.Crumbs as Crumbs
import PyXWF.Errors as Errors
import PyXWF.Registry as Registry
import PyXWF.Namespaces as NS

class StaticNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/crumb/static"

class StaticCrumb(Crumbs.CrumbBase):
    __metaclass__ = Registry.CrumbMeta

    namespace = str(StaticNS)
    names = ["crumb"]

    def __init__(self, site, node):
        super(StaticCrumb, self).__init__(site, node)
        self._document_path = node.get("src")
        self._document_type = node.get("type")

        if self._document_path is None:
            raise Errors.CrumbConfigurationError(
                "{0!s} requires @src attribute".format(type(self)),
                self
            )

        # test whether fetching the document works
        self._get_document()

    def _get_document(self):
        return self.site.file_document_cache.get(
            self._document_path,
            override_mime=self._document_type
        ).doc

    def render(self, ctx, parent):
        return (copy.deepcopy(node) for node in self._get_document().body)
