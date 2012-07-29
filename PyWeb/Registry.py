import itertools
import PyWeb.utils as utils
import abc

class RegistryBase(dict):
    def __setitem__(self, key, cls):
        if key in self:
            raise ValueError("Conflicting key: {0} already taken by {1}".format(key, self[key]))
        super(RegistryBase, self).__setitem__(key, cls)

    def multiReg(self, keys, cls):
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

class _NodePlugins(RegistryBase):
    def getPluginInstance(self, node, site):
        ns, name = utils.splitTag(node.tag)
        cls = self.get(ns, None)
        if cls is None:
            raise KeyError("Unknown plugin namespace: {0}".format(ns))
        return cls(name, node, site)

class _DocumentPlugins(RegistryBase):
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

NodePlugins = _NodePlugins()
DocumentPlugins = _DocumentPlugins()

class NodeMeta(abc.ABCMeta):
    def __new__(mcls, name, bases, dct):
        ns = dct.get("namespace", None)
        if not isinstance(ns, basestring):
            raise TypeError("Plugin needs attribute namespace with a string assigned.")

        cls = abc.ABCMeta.__new__(mcls, name, bases, dct)
        NodePlugins[ns] = cls
        return cls

class DocumentMeta(abc.ABCMeta):
    def __new__(mcls, name, bases, dct):
        types = dct.get("mimeTypes", None)
        try:
            iterable = list(types)
        except TypeError:
            raise TypeError("Plugin needs attribute namespace with a string assigned.")
        cls = abc.ABCMeta.__new__(mcls, name, bases, dct)
        DocumentPlugins.multiReg(iterable, cls)
        return cls
