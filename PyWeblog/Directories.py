from __future__ import unicode_literals

import os, mimetypes, abc, itertools, copy
from datetime import datetime
import time

from PyWeb.utils import ET
import PyWeb.utils as utils
import PyWeb.Registry as Registry
import PyWeb.Navigation as Navigation
import PyWeb.Types as Types
import PyWeb.Errors as Errors
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation
import PyWeb.Namespaces as NS

class BlogFakeDir(Nodes.DirectoryResolutionBehaviour, Nodes.Node, Navigation.Info):
    def __init__(self, blog, parent, name=None, node=None):
        if node is None and name is None:
            raise ValueError("One of name and node must be set")
        super(BlogFakeDir, self).__init__(blog.site, parent, node)
        self.blog = blog
        if node is None:
            self._name = unicode(name)
            self._path = parent.Path + "/" + self._name

    def getTitle(self):
        return self._name

    def getDisplay(self):
        return Navigation.Show if len(self) > 0 else Navigation.Hidden

    def getRepresentative(self):
        return self

    def getNavigationInfo(self, ctx):
        return self

class BlogYearDir(BlogFakeDir):
    def __init__(self, blog, year):
        super(BlogYearDir, self).__init__(blog, blog, str(year))
        self._year = year
        self.months = [None] * 12
        self.monthType = Types.NumericRange(int, 1, 12)

    def _validMonthIter(self, reverse=False):
        if reverse:
            return itertools.ifilter(lambda x: x is not None, reversed(self.months))
        else:
            return itertools.ifilter(lambda x: x is not None, self.months)

    def remove(self, post):
        month = post.creationDate.month
        monthDir = self.months[month]
        monthDir.remove(post)

    def doGet(self, ctx):
        try:
            highestMonth = next(iter(self._validMonthIter(reverse=True)))
        except StopIteration:
            raise Errors.NotFound()
        raise Errors.Found(newLocation=highestMonth.Path)

    def getDisplay(self):
        result = super(BlogYearDir, self).getDisplay()
        if self.blog.combinedStyle and result is Navigation.Show:
            return Navigation.ReplaceWithChildren
        else:
            return result

    def _getChildNode(self, key):
        if key == "":
            return self
        else:
            try:
                return self.months[int(key)]
            except (ValueError, TypeError) as err:
                return None

    def __getitem__(self, month):
        month = self.monthType(month) - 1
        monthObj = self.months[month]
        if monthObj is None:
            monthObj = BlogMonthDir(self, month)
            self.months[month] = monthObj
        return monthObj

    def __iter__(self):
        return iter(self._validMonthIter(reverse=True))

    def __len__(self):
        return sum(1 for _ in self._validMonthIter())

    requestHandlers = {
        "GET": doGet
    }

class BlogMonthDir(BlogFakeDir):
    __metaclass__ = Nodes.NodeMeta

    def __init__(self, yearDir, month):
        super(BlogMonthDir, self).__init__(yearDir.blog, yearDir, str(month))
        self._month = month
        self.pathDict = {}
        self.children = []
        self._fullMonthName = time.strftime("%B %Y",
            (self.parent._year, self._month, 1, 0, 0, 0, 0, 0, -1))
        self._monthName = time.strftime("%B",
            (2000, self._month, 1, 0, 0, 0, 0, 0, -1))

    def add(self, post):
        if post.Name in self.pathDict:
            raise ValueError("Duplicate name: {0}".format(post.Name))
        self.children.append(post)
        self.children.sort(key=lambda x: x.creationDate, reverse=True)
        self.pathDict[post.Name] = post

    def remove(self, post):
        del self.pathDict[post.Name]
        self.children.remove(post)

    def checkNotModified(self, ctx):
        highestTimestamp = None
        # some items might get deleted during this
        for post in list(self.children):  
            post.update()
            if highestTimestamp:
                highestTimestamp = max(post.lastModified, highestTimestamp)
            else:
                highestTimestamp = post.lastModified
        ctx.checkNotModified(highestTimestamp)

    def doGet(self, ctx):
        self.checkNotModified(ctx)
        abstractList = ET.Element(getattr(NS.PyBlog, "abstract-list"), attrib={
            "kind": "month",
            "title": self._fullMonthName
        })
        for post in self.children:
            abstractList.append(post.getAbstract(ctx))
        return self.blog.abstractListTemplate.transform(abstractList, {})

    def getTitle(self):
        if self.blog.combinedStyle:
            return self._fullMonthName
        else:
            return self._monthName

    def _getChildNode(self, key):
        if key == "":
            return self
        return self.pathDict.get(key, None)

    def __iter__(self):
        if self.blog.showPostsInNav:
            return iter(self.children)
        else:
            return iter([])

    def __len__(self):
        return len(self.children)

    requestHandlers = {
        "GET": doGet
    }
