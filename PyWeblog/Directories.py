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
        super(YearDir, self).__init__(blog.site, blog, None)
        self.Blog = blog
        self._name = unicode(year)
        self._path = self.Parent.Path + unicode(year)
        self.year = year
        self._yearstr = unicode(year)
        self._navdisplay = Navigation.Show if blog._nest_months \
                            else Navigation.ReplaceWithChildren
        self._months = [None] * 12

    def _get_child(self, key):
        if key == "":
            newkey = self._get_first_valid_month()
            if newkey is None:
                return None
            raise Errors.Found(local=True, location=unicode(newkey+1))

        try:
            month = int(key)
        except ValueError:
            return None
        if not 1 <= month <= 12:
            return None

        return self._months[month-1]

    def _get_first_valid_month(self):
        for i, month in enumerate(self._months):
            if month is not None:
                return i
        else:
            return None

    def autocreate_month_node(self, month):
        monthidx = month-1
        node = self._months[monthidx]
        if node is None:
            node = MonthDir(self, monthidx+1)
            self._months[monthidx] = node
        node.update_children()
        return node

    def get_navigation_info(self, ctx):
        return self

    def get_title(self):
        return self.yearstr

    def get_display(self):
        return self._navdisplay

    def get_representative(self):
        return self

    def purge_empty(self):
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

    def __init__(self, yearnode, month):
        blog = yearnode.Blog
        super(MonthDir, self).__init__(blog.site, yearnode, None)
        self.Blog = blog
        self.index = blog.index
        self._childmap = {}
        self._children = []
        self._name = unicode(month)
        self._path = self.Parent.Path + unicode(month)
        self.month = month
        self.year = yearnode.year
        # FIXME: allow user/locale defined month names
        self._monthstr = datetime(2000, month, 1).strftime("%B")
        self._monthname = "{0} {1}".format(self._monthstr, yearnode.year)
        if blog._nest_months:
            self._title = self._monthstr
        else:
            self._title = self._monthname

    def _get_child(self, key):
        if key == "":
            return self
        else:
            return self._childmap.get(key, None)

    @property
    def SelectionValue(self):
        return self._monthname

    def do_GET(self, ctx):
        return self.site.template_cache[self.Blog.month_template].transform(
            self.abstracts,
            self.Blog.get_transform_args()
        )

    def get_navigation_info(self, ctx):
        return self

    def get_title(self):
        return self._title

    def get_display(self):
        return Navigation.Show

    def get_representative(self):
        return self

    def get_posts(self):
        return self._children

    def update_children(self):
        abstracts = ET.Element(getattr(NS.PyBlog, "abstract-list"), attrib={
            "month-name": self._monthstr,
            "month": unicode(self.month),
            "year": unicode(self.year)
        })
        self._childmap = {}
        self._children = []
        for post in reversed(self.Blog.index.get_posts_by_month(self.year, self.month)):
            name = post.basename
            if name in self._childmap:
                raise ValueError("Conflict: Duplicate post name: {0}".format(name))
            node = Post.PostNode(self, post)
            self._childmap[name] = node
            self._children.append(node)
            abstracts.append(copy.deepcopy(post.abstract))
        self.abstracts = abstracts

    def __iter__(self):
        if self.Blog.show_posts_in_nav:
            return iter(self._children)
        else:
            return iter([])

    def __len__(self):
        return len(self._children)

    request_handlers = {
        "GET": do_GET
    }



