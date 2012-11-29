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
