"""
This is the heart of the painless plugin registration feature of PyWeb. Herein
defined are the metaclasses responsible for validating and registering plugin
classes and the registries themselves.
"""

import itertools, abc, operator, collections

import PyWeb.utils as utils
import PyWeb.Nodes as Nodes
import PyWeb.Errors as Errors
import PyWeb.Tweaks as Tweaks

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
            raise self.errorClass(ns, name)
        return self._getInstance(cls, node, *args)

    def register(self, ns, names, cls):
        """
        Register the class *cls* for all names in *names* with namespace *ns*.
        """
        keys = list(itertools.izip(itertools.repeat(ns), names))
        self.registerMultiple(keys, cls)

class _NodePlugins(NamespaceRegistry):
    errorClass = Errors.MissingNodePlugin

    def _getInstance(self, cls, node, site, parent):
        return cls(site, parent, node)

class _ParserPlugins(RegistryBase):
    keyDescription = "MIME type"

    def __init__(self):
        super(_ParserPlugins, self).__init__()
        self.instances = {}

    def getPluginInstance(self, mime):
        inst = self.instances.get(mime, None)
        if inst is not None:
            return inst
        cls = self.get(mime, None)
        if cls is None:
            raise Errors.MissingParserPlugin(mime)
        inst = cls(mime)
        self.instances[mime] = inst
        return inst

    def register(self, types, cls):
        self.registerMultiple(types, cls)

class _CrumbPlugins(NamespaceRegistry):
    errorClass = Errors.MissingCrumbPlugin

    def _getInstance(self, cls, node, site):
        return cls(site, node)

class _TweakPlugins(NamespaceRegistry):
    errorClass = Errors.MissingTweakPlugin

    def __setitem__(self, key, cls):
        container = Tweaks.TweakContainer()
        cls._tweaks[key[1]] = container
        super(_TweakPlugins, self).__setitem__(key, container)

    def __call__(self, node):
        ns, name = utils.splitTag(node.tag)
        try:
            container = self[(ns, name)]
        except KeyError:
            raise self.errorClass(ns, name)
        container.append(node)

    _getInstance = None


class HookRegistry(object):
    def __init__(self):
        super(HookRegistry, self).__init__()
        self.hookDict = {}

    def register(self, hookName, handler, priority=0):
        hookList = self.hookDict.setdefault(hookName, [])
        hookList.append((priority, handler))
        hookList.sort(key=operator.itemgetter(0))

    def call(self, hookName, *args):
        handlers = self.hookDict.get(hookName, [])
        collections.deque((handler(*args) for priority, handler in handlers), 0)


class SitletonRegistry(object):
    def __init__(self):
        super(SitletonRegistry, self).__init__()
        self.classes = set()

    def register(self, cls):
        if cls in self.classes:
            raise ValueError("Class {0} already registered as singleton."\
                .format(cls))
        self.classes.add(cls)

    def instanciate(self, site):
        return [cls(site) for cls in self.classes]


NodePlugins = _NodePlugins()
ParserPlugins = _ParserPlugins()
CrumbPlugins = _CrumbPlugins()
TweakPlugins = _TweakPlugins()
Sitletons = SitletonRegistry()
Singletons = dict()

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

        cls = super(NamespaceMetaMixin, mcls).__new__(mcls, name, bases, dct)
        mcls.register(ns, names, cls)
        return cls

class TweakMetaMixin(type):
    """
    Mixin for a metaclass which handles registration of tweak subscriptions,
    based on namespace/tag name pairs.
    """

    def __new__(mcls, name, bases, dct):
        ns = dct.get("tweakNamespace", dct.get("namespace", None))
        try:
            names = list(dct.get("tweakNames", None))
        except TypeError:
            names = []

        dct.setdefault("_tweaks", {})

        cls = super(TweakMetaMixin, mcls).__new__(mcls, name, bases, dct)
        if ns is not None and len(names) > 0:
            mcls.registerTweaks(ns, names, cls)
        return cls

    @classmethod
    def registerTweaks(mcls, ns, names, cls):
        TweakPlugins.register(ns, names, cls)

class NodeMeta(Nodes.NodeMeta, NamespaceMetaMixin):
    """
    Takes :cls:`PyWeb.Nodes.NodeMeta` and mixes it with the
    :cls:`NamespaceMetaMixin` to create a suitable Node plugin metaclass.
    """
    @classmethod
    def register(mcls, ns, names, cls):
        NodePlugins.register(ns, names, cls)

class ParserMeta(abc.ABCMeta, TweakMetaMixin):
    """
    Metaclass for parsers. Parser classes need to have a
    *mimeTypes* attribute which must be an iterable of strings reflecting the
    mime types the class is able to handle.
    """
    def __new__(mcls, name, bases, dct):
        types = dct.get("mimeTypes", None)
        try:
            iterable = list(types)
        except TypeError:
            raise TypeError("Plugin needs attribute mimeTypes which must be a sequence of strings.")
        cls = super(ParserMeta, mcls).__new__(mcls, name, bases, dct)
        ParserPlugins.register(iterable, cls)
        return cls

class CrumbMeta(abc.ABCMeta, NamespaceMetaMixin):
    """
    Takes :cls:`abc.ABCMeta` and mixes it with the
    :cls:`NamespaceMetaMixin` to create a suitable Crumb plugin metaclass.
    """
    @classmethod
    def register(mcls, ns, names, cls):
        CrumbPlugins.register(ns, names, cls)


class SitletonMeta(abc.ABCMeta, TweakMetaMixin):
    """
    A class using this metaclass will have exactly one instance per running
    site. Thus, this metaclass is useful for use with hook classes which
    register hooks on a site and do nothing else.
    """

    def __new__(mcls, name, bases, dct):
        cls = super(SitletonMeta, mcls).__new__(mcls, name, bases, dct)
        Sitletons.register(cls)
        return cls

def clearAll():
    NodePlugins.clear()
    TweakPlugins.clear()
    ParserPlugins.clear()
    CrumbPlugins.clear()
