class __metaclass__(type):
    def _notInstanciable(mcls, cls):
        raise TypeError("Cannot instanciate {0}".format(cls.__name__))
    
    def __new__(mcls, name, bases, dct):
        dct["__new__"] = mcls._notInstanciable
        cache = dct.get("cache", list())
        dct["cache"] = dict()
        cls = type.__new__(mcls, name, bases, dct)
        # prepopulate cache
        for entry in cache:
            getattr(cls, entry)
        return cls
    
    def __getattr__(cls, name):
        cache = cls.__dict__["cache"]
        try:
            return cache[name]
        except KeyError:
            attr = "{{{0}}}{1}".format(cls.xmlns, name)
            cache[name] = attr
        return attr

    def __str__(cls):
        return cls.__dict__["xmlns"]

    def __unicode__(cls):
        return unicode(cls.__dict__["xmlns"])


class XHTML(object):
    __metaclass__ = __metaclass__
    xmlns = "http://www.w3.org/1999/xhtml"
    cache = ["a", "head", "title", "body"]
    
xhtml = XHTML

class PyWebXML(object):
    __metaclass__ = __metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/documents/pywebxml"
    cache = ["a"]

class Site(object):
    __metaclass__ = __metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/site"
    cache = ["meta", "site", "tree"]
