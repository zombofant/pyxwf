from __future__ import unicode_literals
import PyWeb.Namespaces as NS

class PyBlog(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/weblog"
NS.PyBlog = PyBlog

import PyWeblog.Node
