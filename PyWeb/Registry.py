import itertools, abc

import PyWeb.utils as utils
import PyWeb.Nodes as Nodes

class RegistryBase(dict):
    keyDescription = "key"
    
    def __setitem__(self, key, cls):
        if key in self:
            raise ValueError("Conflicting {2}: {0} already taken by {1}".format(key, self[key], self.keyDescription))
        super(RegistryBase, self).__setitem__(key, cls)

    def registerMultiple(self, keys, cls):
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
    keyDescription = "namespace/name pair"
    
    def getPluginInstance(self, node, *args):
        ns, name = utils.splitTag(node.tag)
        cls = self.get((ns, name), None)
        if cls is None:
            raise KeyError("Unknown plugin namespace: {0}".format(ns))
        return self._getInstance(cls, node, *args)

    def register(self, ns, names, cls):
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
    @classmethod
    def register(mcls, ns, names, cls):
        NodePlugins.register(ns, names, cls)

class DocumentMeta(abc.ABCMeta):
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
    @classmethod
    def register(mcls, ns, names, cls):
        CrumbPlugins.register(ns, names, cls)
