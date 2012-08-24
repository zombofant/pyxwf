import os, tempfile, shutil, unittest

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Site as Site
import PyWeb.Context as Context
import PyWeb.Namespaces as NS

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

class MockNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/for-unit-testing-only"

class MockFSLocation(object):
    def __init__(self):
        self._closed = False
        self._root = tempfile.mkdtemp(".mock")

    def __del__(self):
        self.close()

    def _unclosed(self):
        if self._closed:
            raise ValueError("This operation is not allowed on closed FS locations.")

    @property
    def Root(self):
        self._unclosed()
        return self._root

    def open(self, fileName, mode):
        return open(self(fileName), mode)

    def __call__(self, fileName):
        return os.path.join(self.Root, fileName)

    def close(self):
        if self._closed:
            return
        self._closed = True
        shutil.rmtree(self._root)


class MockedSite(Site.Site):
    def __init__(self, fsLocation, sitemapRelFileName="sitemap.xml"):
        os.chdir(fsLocation.Root)
        sitemapFile = fsLocation(sitemapRelFileName)
        super(MockedSite, self).__init__(sitemapFile, defaultURLRoot="/")


class MockedContext(Context.Context):
    @classmethod
    def fromSite(cls, site, **kwargs):
        return cls(site.urlRoot, **kwargs)

    def __init__(self, urlRoot,
            method="GET",
            path="",
            responseStream=StringIO(),
            scheme="http",
            host="mockingbird.example.com",
            userAgent="Wget/1.12 (linux-gnu)",
            accept="application/xhtml+xml",
            ifModifiedSince=None,
            queryData={}):
        super(MockedContext, self).__init__(
            method,
            path,
            responseStream
        )
        self._fullURI = urlRoot + path
        self._scheme = scheme
        self._hostName = host
        self.parsePreferencesList(accept)
        self._canUseXHTML = self.getContentTypeToUse(["application/xhtml+xml", "text/xhtml"], False) is not None
        self._ifModifiedSince = ifModifiedSince
        self._queryData = {}

    def _requireQuery(self):
        pass

    def sendResponse(self, message):
        out = self.Out
        out.write(b"{0:d} Mocked Status Code\n".format(message.StatusCode))
        self.setResponseContentType(message.MIMEType, message.Encoding)
        self._setCacheHeaders()
        for header, value in self._responseHeaders.items():
            out.write("{0}: {1}\n".format(header, ",".join(value)).encode("ascii"))
        out.write(b"\n")
        self.Out.write(message.getEncodedBody())


class ContextTest(unittest.TestCase):
    def tearDown(self):
        del self.ctx
        super(ContextTest, self).tearDown()


class FSTest(unittest.TestCase):
    def setUp(self):
        super(FSTest, self).setUp()
        self.fs = MockFSLocation()

    def tearDown(self):
        self.fs.close()
        del self.fs
        super(FSTest, self).tearDown()


class DynamicSiteTest(FSTest):
    sitemapXML = """<?xml version="1.0" encoding="utf-8"?>
<site   xmlns="http://pyweb.zombofant.net/xmlns/site"
        xmlns:py="http://pyweb.zombofant.net/xmlns/documents/pywebxml"
        xmlns:dir="http://pyweb.zombofant.net/xmlns/nodes/directory"
        xmlns:page="http://pyweb.zombofant.net/xmlns/nodes/page"
        xmlns:redirect="http://pyweb.zombofant.net/xmlns/nodes/redirect">
    <meta>
        <title>mocked site</title>
        <urlRoot>/</urlRoot>
    </meta>
    <plugins>
        <p>PyWeb.Nodes.Redirect</p>
        <p>PyWeb.Nodes.Directory</p>
    </plugins>
    <tweaks />
    <dir:tree
            id="treeRoot">
    </dir:tree>
    <crumbs />
</site>""".encode("utf-8")

    def getBasicSitemap(self):
        sitemap = ET.XML(self.sitemapXML)
        meta = sitemap.find(NS.Site.meta)
        plugins = sitemap.find(NS.Site.plugins)
        tweaks = sitemap.find(NS.Site.tweaks)
        for child in sitemap:
            tag = child.tag
            if not isinstance(tag, basestring):
                continue
            ns, name = utils.splitTag(tag)
            if name == "tree":
                tree = child
                break
        else:
            tree = None
        crumbs = sitemap.find(NS.Site.crumbs)
        return sitemap, meta, plugins, tweaks, tree, crumbs

    def getSitemap(self, setupFunc, **kwargs):
        sitemapData = self.getBasicSitemap()
        sitemap = sitemapData[0]
        setupFunc(*sitemapData, **kwargs)
        return sitemap

    def setupSite(self, sitemap):
        f = self.fs.open("sitemap.xml", "w")
        try:
            f.write(ET.tostring(sitemap))
        finally:
            f.close()
        self.site = MockedSite(self.fs)

    def tearDown(self):
        if hasattr(self, "site"):
            del self.site
        super(DynamicSiteTest, self).tearDown()

class SiteTest(DynamicSiteTest):
    def setUpFS(self):
        pass

    def setUpSitemap(self, etree, meta, plugins, tweaks, tree, crumbs):
        ET.SubElement(tree, "{http://pyweb.zombofant.net/xmlns/nodes/redirect}internal", attrib={
            "id": "foo",
            "to": "bar"
        })
        ET.SubElement(tree, "{http://pyweb.zombofant.net/xmlns/nodes/redirect}internal", attrib={
            "id": "bar",
            "to": "foo",
            "name": "bar"
        })

    def setUp(self):
        super(SiteTest, self).setUp()
        self.setUpFS()
        sitemap = self.getSitemap(self.setUpSitemap)
        self.setupSite(sitemap)

    def tearDown(self):
        del self.site
        super(SiteTest, self).tearDown()
