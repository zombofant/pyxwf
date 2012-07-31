"""
This is the heart of the painless plugin registration feature of PyWeb. Herein
defined are the metaclasses responsible for validating and registering plugin
classes and the registries themselves.
"""

import itertools, abc

import PyWeb.utils as utils
import PyWeb.Nodes as Nodes

class RegistryBase(dict):
    """
    Base class for the registries defined herein. An end user will never have to
    do anything with these classes.

    Developers may want to subclass this one if they *really* need to introduce
    a new registry to PyWeb.
    """
    
    keyDescription = "key"
    
    def __setitem__(self, key, cls):
        if key in self:
            raise ValueError("Conflicting {2}: {0} already taken by {1}".format(key, self[key], self.keyDescription))
        super(RegistryBase, self).__setitem__(key, cls)

    def registerMultiple(self, keys, cls):
        """
        Iterate over keys and set each key to cls in self.
        """
        try:
            lastSuccessful = None
            for key in keys:
                self[key] = cls
                lastSuccessful = key
        except:
            if lastSuccessful is not None:
                for key in itertools.takewhile(lambda x: x is not lastSuccessful, keys):
                    del self[key]
            raise
            
    def __call__(self, *args, **kwargs):
        return self.getPluginInstance(*args, **kwargs)

class NamespaceRegistry(RegistryBase):
    """
    A more specialized baseclass for registries dealing with namespace/tagname
    pairs for XML nodes.
    """
    keyDescription = "namespace/name pair"
    
    def getPluginInstance(self, node, *args):
        ns, name = utils.splitTag(node.tag)
        cls = self.get((ns, name), None)
        if cls is None:
            raise KeyError("Unknown plugin: {1} in {0}".format(ns, name))
        return self._getInstance(cls, node, *args)

    def register(self, ns, names, cls):
        """
        Register the class *cls* for all names in *names* with namespace *ns*.
        """
        keys = list(itertools.izip(itertools.repeat(ns), names))
        self.registerMultiple(keys, cls)

class _NodePlugins(NamespaceRegistry):
    def _getInstance(self, cls, node, site, parent):
        return cls(site, parent, node)

class _DocumentPlugins(RegistryBase):
    keyDescription = "MIME type"
    
    def __init__(self):
        super(_DocumentPlugins, self).__init__()
        self.instances = {}
    
    def getPluginInstance(self, mime):
        inst = self.instances.get(mime, None)
        if inst is not None:
            return inst
        cls = self.get(mime, None)
        if cls is None:
            raise KeyError("No Document handler for MIME type: {0}".format(mime))
        inst = cls(mime)
        self.instances[mime] = inst
        return inst

    def register(self, types, cls):
        self.registerMultiple(types, cls)

class _CrumbPlugins(NamespaceRegistry):
    def _getInstance(self, cls, node, site):
        return cls(site, node)

NodePlugins = _NodePlugins()
DocumentPlugins = _DocumentPlugins()
CrumbPlugins = _CrumbPlugins()

class NamespaceMetaMixin(type):
    """
    Mixin for a metaclass which handles registration of classes which register
    based on namespace/tag name pairs.

    It requires that the class has a *namespace* attribute which has to be
    a valid XML namespace as a string and a *names* attribute which must be an
    iterable of strings which must all be valid XML node tags.

    The class will be registered for all names in the given namespace.
    """
    defaultNames = []
    
    def __new__(mcls, name, bases, dct):
        ns = dct.get("namespace", None)
        try:
            names = list(dct.get("names", mcls.defaultNames))
        except TypeError:
            raise TypeError("Plugin needs names attribute which must be convertible to a sequence.")
        if not isinstance(ns, basestring):
            raise TypeError("Plugin needs attribute namespace with a string assigned.")
        if len(names) == 0:
            raise ValueError("Plugins must register for at least one name.")

        cls = type.__new__(mcls, name, bases, dct)
        mcls.register(ns, names, cls)
        return cls

class NodeMeta(Nodes.NodeMeta, NamespaceMetaMixin):
    """
    Takes :cls:`PyWeb.Nodes.NodeMeta` and mixes it with the
    :cls:`NamespaceMetaMixin` to create a suitable Node plugin metaclass.
    """
    @classmethod
    def register(mcls, ns, names, cls):
        NodePlugins.register(ns, names, cls)

class DocumentMeta(abc.ABCMeta):
    """
    Metaclass for document types. Document type classes need to have a
    *mimeTypes* attribute which must be an iterable of strings reflecting the
    mime types the class is able to handle.
    """
    def __new__(mcls, name, bases, dct):
        types = dct.get("mimeTypes", None)
        try:
            iterable = list(types)
        except TypeError:
            raise TypeError("Plugin needs attribute namespace with a string assigned.")
        cls = abc.ABCMeta.__new__(mcls, name, bases, dct)
        DocumentPlugins.register(iterable, cls)
        return cls

class CrumbMeta(abc.ABCMeta, NamespaceMetaMixin):
    """
    Takes :cls:`abc.ABCMeta` and mixes it with the
    :cls:`NamespaceMetaMixin` to create a suitable Crumb plugin metaclass.
    """
    @classmethod
    def register(mcls, ns, names, cls):
        CrumbPlugins.register(ns, names, cls)
