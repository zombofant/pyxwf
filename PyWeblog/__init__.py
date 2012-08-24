from __future__ import unicode_literals
import PyXWF.Namespaces as NS

class PyBlog(object):
    __metaclass__ = NS.__metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/weblog"
NS.PyBlog = PyBlog

import PyWeblog.Node
