from __future__ import unicode_literals, absolute_import, print_function

from datetime import datetime
import functools, copy

from PyXWF.utils import ET
import PyXWF.Nodes as Nodes
import PyXWF.Navigation as Navigation
import PyXWF.Errors as Errors
import PyXWF.Namespaces as NS

import PyWeblog.Post as Post
import PyWeblog.Protocols as Protocols

@functools.total_ordering
class YearDir(Nodes.DirectoryResolutionBehaviour, Nodes.Node, Navigation.Info):
    def __init__(self, blog, year):
        super(YearDir, self).__init__(blog.Site, blog, None)
        self.Blog = blog
        self._name = unicode(year)
        self._path = self.Parent.Path + unicode(year)
        self.year = year
        self._yearStr = unicode(year)
        self._navDisplay = Navigation.Show if blog._nestMonths \
                            else Navigation.ReplaceWithChildren
        self._months = [None] * 12

    def _getChildNode(self, key):
        if key == "":
            newKey = self._getFirstValidMonth()
            if newKey is None:
                return None
            raise Errors.Found(local=True, location=unicode(newKey+1))

        try:
            month = int(key)
        except ValueError:
            return None
        if not 1 <= month <= 12:
            return None

        return self._months[month-1]

    def _getFirstValidMonth(self):
        for i, month in enumerate(self._months):
            if month is not None:
                return i
        else:
            return None

    def autocreateMonthNode(self, month):
        monthIdx = month-1
        node = self._months[monthIdx]
        if node is None:
            node = MonthDir(self, monthIdx+1)
            self._months[monthIdx] = node
        node.updateChildren()
        return node

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self.yearStr

    def getDisplay(self):
        return self._navDisplay

    def getRepresentative(self):
        return self

    def purgeEmpty(self):
        for i, month in enumerate(self._months):
            if month is None:
                continue
            if len(month) == 0:
                self._months[i] = None

    def __iter__(self):
        return (month for month in reversed(self._months) if month is not None)

    def __len__(self):
        return sum(1 for month in self._months if month is not None)

    def __lt__(self, other):
        try:
            return self.year < other.year
        except AttributeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.year <= other.year
        except AttributeError:
            return NotImplemented

    def __eq__(self, other):
        try:
            return self.year == other.year
        except AttributeError:
            return NotImplemented

class MonthDir(Nodes.DirectoryResolutionBehaviour, Nodes.Node, Navigation.Info,
        Protocols.PostDirectory):

    SelectionCriterion = "month"

    def __init__(self, yearNode, month):
        blog = yearNode.Blog
        super(MonthDir, self).__init__(blog.Site, yearNode, None)
        self.Blog = blog
        self.index = blog.index
        self._childMap = {}
        self._children = []
        self._name = unicode(month)
        self._path = self.Parent.Path + unicode(month)
        self.month = month
        self.year = yearNode.year
        # FIXME: allow user/locale defined month names
        self._monthStr = datetime(2000, month, 1).strftime("%B")
        self._monthName = "{0} {1}".format(self._monthStr, yearNode.year)
        if blog._nestMonths:
            self._title = self._monthStr
        else:
            self._title = self._monthName

    def _getChildNode(self, key):
        if key == "":
            return self
        else:
            return self._childMap.get(key, None)

    @property
    def SelectionValue(self):
        return self._monthName

    def doGet(self, ctx):
        return self.Site.templateCache[self.Blog.monthTemplate].transform(
            self.abstracts,
            self.Blog.getTransformArgs()
        )

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self._title

    def getDisplay(self):
        return Navigation.Show

    def getRepresentative(self):
        return self

    def getPosts(self):
        return self._children

    def updateChildren(self):
        abstracts = ET.Element(getattr(NS.PyBlog, "abstract-list"), attrib={
            "month-name": self._monthStr,
            "month": unicode(self.month),
            "year": unicode(self.year)
        })
        self._childMap.clear()
        self._children = []
        for post in reversed(self.Blog.index.getPostsByMonth(self.year, self.month)):
            name = post.basename
            if name in self._childMap:
                raise ValueError("Conflict: Duplicate post name: {0}".format(name))
            node = Post.PostNode(self, post)
            self._childMap[name] = node
            self._children.append(node)
            abstracts.append(copy.deepcopy(post.abstract))
        self.abstracts = abstracts

    def __iter__(self):
        if self.Blog.showPostsInNav:
            return iter(self._children)
        else:
            return iter([])

    def __len__(self):
        return len(self._children)

    requestHandlers = {
        "GET": doGet
    }



