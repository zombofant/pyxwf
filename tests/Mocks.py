import os, tempfile, shutil, unittest

import PyWeb.Site as Site

class MockFSLocation(object):
    def __init__(self):
        self._closed = False
        self._root = tempfile.mkdtemp(".mock")
        self._sitedir = os.path.join(self._root, "site")
        os.mkdir(self._sitedir)

    def __del__(self):
        self.close()

    def _unclosed(self):
        if self._closed:
            raise ValueError("This operation is not allowed on closed FS locations.")

    @property
    def Root(self):
        self._unclosed()
        return self._root

    @property
    def SiteDir(self):
        self._unclosed()
        return self._sitedir

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
        os.chdir(fsLocation.SiteDir)
        sitemapFile = os.path.join(fsLocation.SiteDir, sitemapRelFileName)
        super(MockedSite, Site).__init__(sitemapFile, defaultURLRoot="/")


class FSTest(unittest.TestCase):
    def setUp(self):
        self.fs = MockFSLocation()

    def tearDown(self):
        self.fs.close()
        del self.fs
