import os, tempfile, shutil, unittest

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Site as Site
import PyXWF.Context as Context
import PyXWF.Namespaces as NS

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

class MockNS(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/for-unit-testing-only"

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
            responseStream=None,
            scheme="http",
            host="mockingbird.example.com",
            userAgent="Wget/1.12 (linux-gnu)",
            accept="application/xhtml+xml",
            acceptCharset="utf-8",
            ifModifiedSince=None,
            queryData={}):
        super(MockedContext, self).__init__()
        self._method = method
        self._path = path
        self._outfile = responseStream or StringIO()
        self._fullURI = urlRoot + path
        self._scheme = scheme
        self._hostName = host
        self._accept = self.parseAccept(accept)
        self._acceptCharset = self.parseAcceptCharset(acceptCharset)
        self._determineHTMLContentType()
        self._ifModifiedSince = ifModifiedSince
        self._queryData = {}

    @property
    def Out(self):
        return self._outfile

    def _requireQuery(self):
        pass

    def sendResponse(self, message):
        out = self.Out
        body = self.getEncodedBody(message)
        out.write(b"{0:d} {1}\n".format(message.Status.code, message.Status.title))
        self.setResponseContentType(message.MIMEType, message.Encoding)
        self._setCacheStatus()
        self._setPropertyHeaders()
        # sorting is important to create reproducible and easy to test responses
        for header, value in sorted(self._responseHeaders.items()):
            out.write("{0}: {1}\n".format(header, value).encode("ascii"))
        out.write(b"\n")
        self.Out.write(body)


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
<site   xmlns="http://pyxwf.zombofant.net/xmlns/site"
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:dir="http://pyxwf.zombofant.net/xmlns/nodes/directory"
        xmlns:page="http://pyxwf.zombofant.net/xmlns/nodes/page"
        xmlns:redirect="http://pyxwf.zombofant.net/xmlns/nodes/redirect">
    <meta>
        <title>mocked site</title>
        <urlRoot>/</urlRoot>
    </meta>
    <plugins>
        <p>PyXWF.Nodes.Redirect</p>
        <p>PyXWF.Nodes.Directory</p>
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

    def setUpSitemap(self, etree, meta, plugins, tweaks, tree, crumbs):
        ET.SubElement(tree, "{http://pyxwf.zombofant.net/xmlns/nodes/redirect}internal", attrib={
            "id": "foo",
            "to": "bar"
        })
        ET.SubElement(tree, "{http://pyxwf.zombofant.net/xmlns/nodes/redirect}internal", attrib={
            "id": "bar",
            "to": "foo",
            "name": "bar"
        })

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

    def setUp(self):
        super(SiteTest, self).setUp()
        self.setUpFS()
        sitemap = self.getSitemap(self.setUpSitemap)
        self.setupSite(sitemap)

    def tearDown(self):
        del self.site
        super(SiteTest, self).tearDown()
