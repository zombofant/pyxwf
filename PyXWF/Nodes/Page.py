# File name: Page.py
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
import os

import PyXWF.Nodes as Nodes
import PyXWF.Registry as Registry
import PyXWF.Navigation as Navigation
import PyXWF.Document as Document
import PyXWF.Resource as Resource
import PyXWF.Namespaces as NS

class PageNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/nodes/page"

class Page(Nodes.Node, Navigation.Info, Resource.Resource):
    __metaclass__ = Registry.NodeMeta

    namespace = str(PageNS)
    names = ["node"]

    def __init__(self, site, parent, node):
        super(Page, self).__init__(site, parent, node)

        self._navtitle = self._navtitle_with_none_type(node.get("nav-title"))
        self._navdisplay = Navigation.DisplayMode(node.get("nav-display", Navigation.Show))
        self.mimetype = node.get("type")
        self.filename = os.path.join(site.root, node.get("src"))
        self._last_modified = None
        self.title = None

    @property
    def LastModified(self):
        return self._last_modified

    def update(self):
        # this is pretty lazy; it will not load the document but only retrieve
        # the datetime object from the file system
        doc_last_modified = self.site.file_document_cache\
                .get_last_modified(self.filename)
        if self._last_modified is None or doc_last_modified is None or \
                self._last_modified < doc_last_modified:
            docproxy = self.site.file_document_cache.get(self.filename, self.mimetype)
            docproxy.update()
            doc = docproxy.doc
            self._last_modified = doc_last_modified
            self.title = self._navtitle or doc.title

    def _get_docproxy(self):
        return self.site.file_document_cache.get(self.filename, self.mimetype)

    def do_GET(self, ctx):
        return self._get_docproxy().doc

    def resolve_path(self, ctx, relpath):
        ctx.use_resource(self)
        return super(Page, self).resolve_path(ctx, relpath)

    def get_title(self):
        return self.title

    def get_display(self):
        return self._navdisplay

    def get_representative(self):
        return self

    def get_navigation_info(self, ctx):
        if self.title is None:
            self.threadsafe_update()
        return self

    request_handlers = {
        "GET": do_GET
    }
