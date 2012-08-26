"""
This is the heart of the painless plugin registration feature of PyXWF. Herein
defined are the metaclasses responsible for validating and registering plugin
classes and the registries themselves.
"""

import itertools, abc, operator, collections

import PyXWF.utils as utils
import PyXWF.Nodes as Nodes
import PyXWF.Errors as Errors
import PyXWF.Tweaks as Tweaks

class RegistryBase(dict):
    """
    Base class for the registries defined herein. An end user will never have to
    do anything with these classes.

    Developers may want to subclass this one if they *really* need to introduce
    a new registry to PyXWF.
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

class _CrumbPlugins(NamespaceRegistry):
    errorClass = Errors.MissingCrumbPlugin

    def _getInstance(self, cls, node, site):
        return cls(site, node)

class HookRegistry(object):
    def __init__(self):
        super(HookRegistry, self).__init__()
        self.hookDict = {}

    def register(self, hookName, handler, priority=0):
        hookList = self.hookDict.setdefault(hookName, [])
        hookList.append((priority, handler))
        # hookList.sort(key=operator.itemgetter(0))

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


class ParserRegistry(object):
    def __init__(self):
        super(ParserRegistry, self).__init__()
        self._mimeMap = {}

    def register(self, inst, mimeTypes):
        try:
            inst.parse
        except AttributeError:
            raise TypeError("Parsers must have the parse() method.")
        for mimeType in mimeTypes:
            if mimeType in self._mimeMap:
                raise PluginConflict(mimeType, self._mimeMap[mimeType], inst, "parsing of mime type {0}".format(mimeType))
            self._mimeMap[mimeType] = inst

    def __getitem__(self, mimeType):
        try:
            return self._mimeMap[mimeType]
        except KeyError:
            raise Errors.MissingParserPlugin(mimeType)


class TweakRegistry(object):
    def __init__(self):
        super(TweakRegistry, self).__init__()
        self._tweaks = {}

    def register(self, inst, hooks):
        for ns, (name, hook) in hooks:
            tag = "{{{0}}}{1}".format(ns, name)
            if tag in self._tweaks:
                raise PluginConflict(tag, self._tweaks[tag], inst, "tweak node {0}".format(tag))
            self._tweaks[tag] = hook

    def submitTweak(self, node):
        try:
            hook = self._tweaks[node.tag]
        except KeyError:
            raise Errors.MissingTweakPlugin(node.tag)
        hook(node)

    _getInstance = None

NodePlugins = _NodePlugins()
CrumbPlugins = _CrumbPlugins()
Sitletons = SitletonRegistry()

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

class NodeMeta(Nodes.NodeMeta, NamespaceMetaMixin):
    """
    Takes :class:`~PyXWF.Nodes.NodeMeta` and mixes it with the
    :class:`NamespaceMetaMixin` to create a suitable Node plugin metaclass.

    .. note::
        See :class:`~PyXWF.Nodes.Node` for an example of use.
    """
    @classmethod
    def register(mcls, ns, names, cls):
        NodePlugins.register(ns, names, cls)

class CrumbMeta(abc.ABCMeta, NamespaceMetaMixin):
    """
    Takes :class:`abc.ABCMeta` and mixes it with the
    :class:`NamespaceMetaMixin` to create a suitable Crumb plugin metaclass.

    .. note::
        See :class:`~PyXWF.Crumbs.CrumbBase` for an example of use.
    """
    @classmethod
    def register(mcls, ns, names, cls):
        CrumbPlugins.register(ns, names, cls)


class SitletonMeta(abc.ABCMeta):
    """
    A class using this metaclass will have exactly one instance per running
    site. Thus, this metaclass is useful for use with hook classes which
    register hooks on a site and do nothing else.
    """

    def __new__(mcls, name, bases, dct):
        cls = super(SitletonMeta, mcls).__new__(mcls, name, bases, dct)
        Sitletons.register(cls)
        return cls
