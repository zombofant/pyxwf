from __future__ import unicode_literals

from PyWeb.utils import ET
import PyWeb.Types as Types
import PyWeb.Nodes as Nodes
import PyWeb.Navigation as Navigation
import PyWeb.Namespaces as NS

class LandingPage(Nodes.Node, Navigation.Info):
    __metaclass__ = Nodes.NodeMeta

    def __init__(self, blog, node):
        super(LandingPage, self).__init__(blog.site, blog, node)
        if self._name != "":
            raise ValueError("Invalid landing page name.")
        self.blog = blog
        self.template = blog.landingPageTemplate
        self.recentCount = Types.DefaultForNone(3,
            Types.NumericRange(Types.Typecasts.int, 1, None)
        )(node.get("post-count"))

    def doGet(self, ctx):
        articles = ET.Element(getattr(NS.PyBlog, "abstract-list"))
        for recentPost in self.blog.iterRecent(self.recentCount):
            articles.append(recentPost.getAbstract(ctx))
        return self.template.transform(articles, {})

    def getNavigationInfo(self, ctx):
        return self

    def getTitle(self):
        return self.blog.getTitle()

    def getDisplay(self):
        return self.blog.getDisplay()

    def getRepresentative(self):
        return self

    requestHandlers = {
        "GET": doGet
    }
