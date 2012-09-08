import os
import tempfile
import shutil
import unittest
import logging

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Site as Site
import PyXWF.Context as Context
import PyXWF.Namespaces as NS
import PyXWF.Resource as Resource

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

    def open(self, filename, mode):
        return open(self(filename), mode)

    def __call__(self, filename):
        return os.path.join(self.Root, filename)

    def close(self):
        if self._closed:
            return
        self._closed = True
        shutil.rmtree(self._root)


class MockedSite(Site.Site):
    def __init__(self, fslocation, sitemap_relative_filename="sitemap.xml"):
        os.chdir(fslocation.Root)
        sitemap_file = fslocation(sitemap_relative_filename)
        super(MockedSite, self).__init__(sitemap_file, default_url_root="/")


class MockedContext(Context.Context):
    @classmethod
    def from_site(cls, site, **kwargs):
        return cls(site.urlroot, **kwargs)

    def __init__(self, urlroot,
            method="GET",
            path="",
            response_stream=None,
            scheme="http",
            host="mockingbird.example.com",
            useragent="Wget/1.12 (linux-gnu)",
            accept="application/xhtml+xml",
            accept_charset="utf-8",
            if_modified_since=None,
            query_data={}):
        super(MockedContext, self).__init__()
        self._method = method
        self._path = path
        self._outfile = response_stream or StringIO()
        self._fulluri = urlroot + path
        self._scheme = scheme
        self._hostname = host
        self._accept = self.parse_accept(accept)
        self._accept_charset = self.parse_accept_charset(accept_charset)
        self._determine_html_content_type()
        self._if_modified_since = if_modified_since
        self._query_data = query_data

    @property
    def Out(self):
        return self._outfile

    def _require_query(self):
        pass

    def _require_post(self):
        self._post_data = {}

    def _require_cookies(self):
        self._cookie_data = {}

    def send_response(self, message):
        out = self.Out
        body = self.get_encoded_body(message)
        out.write(b"{0:d} {1}\n".format(message.Status.code, message.Status.title))
        self.set_response_content_type(message.MIMEType, message.Encoding)
        self._set_cache_status()
        self._set_property_headers()
        # sorting is important to create reproducible and easy to test responses
        for header, values in sorted(self._response_headers.items()):
            for value in values:
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
    sitemap_xml = """<?xml version="1.0" encoding="utf-8"?>
<site   xmlns="http://pyxwf.zombofant.net/xmlns/site"
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:dir="http://pyxwf.zombofant.net/xmlns/nodes/directory"
        xmlns:page="http://pyxwf.zombofant.net/xmlns/nodes/page"
        xmlns:redirect="http://pyxwf.zombofant.net/xmlns/nodes/redirect">
    <meta>
        <title>mocked site</title>
        <urlroot>/</urlroot>
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

    def get_basic_sitemap(self):
        sitemap = ET.XML(self.sitemap_xml)
        meta = sitemap.find(NS.Site.meta)
        plugins = sitemap.find(NS.Site.plugins)
        tweaks = sitemap.find(NS.Site.tweaks)
        for child in sitemap:
            tag = child.tag
            if not isinstance(tag, basestring):
                continue
            ns, name = utils.split_tag(tag)
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

    def get_sitemap(self, setup_func, **kwargs):
        sitemap_data = self.get_basic_sitemap()
        sitemap = sitemap_data[0]
        setup_func(*sitemap_data, **kwargs)
        return sitemap

    def setup_site(self, sitemap):
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
    def setup_fs(self):
        pass

    def setUp(self):
        super(SiteTest, self).setUp()
        self.setup_fs()
        sitemap = self.get_sitemap(self.setUpSitemap)
        self.setup_site(sitemap)

    def tearDown(self):
        del self.site
        super(SiteTest, self).tearDown()

class FakeResource(Resource.Resource):
    @property
    def LastModified(self):
        return self._last_modified

    @LastModified.setter
    def LastModified(self, value):
        self._last_modified = value

    def update(self):
        pass

# as per http://stackoverflow.com/a/1049375/1248008
class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""

    def __init__(self, *args, **kwargs):
        self.reset()
        super(MockLoggingHandler, self).__init__(*args, **kwargs)

    def _getMessageList(self, levelname):
        return self.messages.setdefault(levelname, [])

    def emit(self, record):
        msgs = self._getMessageList(record.levelname.lower())
        msgs.append(record.getMessage())

    def reset(self):
        self.messages = {}

    def getMessageCount(self, levelname):
        return len(self._getMessageList(levelname.lower()))

    def findAndRemoveMessage(self, levelname, message):
        self._getMessageList(levelname).remove(message)

class MockLogging(object):
    def __init__(self, logger=logging.getLogger(), level=logging.NOTSET):
        self._mocked_logging = MockLoggingHandler(level=level)
        self._logger = logger

    def __enter__(self):
        _root_logger = logging.getLogger()
        if self._logger is _root_logger:
            self._stdout_handler = _root_logger.handlers[0]
            _root_logger.removeHandler(self._stdout_handler)
        else:
            self._stdout_handler = None
            self._logger.propagate = False
        self._logger.addHandler(self._mocked_logging)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._logger.removeHandler(self._mocked_logging)
        self._mocked_logging.reset()
        if self._stdout_handler is not None:
            self._logger.addHandler(self._stdout_handler)
        else:
            self._logger.propagate = True

    def assertLoggedCount(self, levelname, count):
        if self._mocked_logging.getMessageCount(levelname) != count:
            raise AssertionError("Amount of logged messages differs")

    def assertLoggedMessage(self, levelname, message):
        try:
            self._mocked_logging.findAndRemoveMessage(levelname, message)
        except (IndexError, ValueError):
            raise AssertionError("Message has not been logged: {0!r}".format(message))
