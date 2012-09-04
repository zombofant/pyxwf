import abc, collections

import PyXWF.utils as utils
import PyXWF.Errors as Errors
import PyXWF.Types as Types
import PyXWF.ContentTypes as ContentTypes

class NodeMeta(abc.ABCMeta):
    """
    Metaclass which deals with enforcing the existance of the *requestHandlers*
    attribute and its contents.

    .. note::
        You don't use this metaclass usually. To create a complete node class,
        you need the :class:`PyXWF.Registry.NodeMeta` metaclass.
    """

    @classmethod
    def _raiseNoValidRequestHandlers(mcls, name):
        raise TypeError("{0} requires requestHandlers as dict (or dict-compatible) or callable".format(name))

    def __new__(mcls, name, bases, dct):
        try:
            requestHandlers = dct["requestHandlers"]
        except KeyError:
            for base in bases:
                try:
                    requestHandlers = base.requestHandlers
                    break;
                except AttributeError:
                    pass
            else:
                mcls._raiseNoValidRequestHandlers(name)
        if requestHandlers is None:
            raise TypeError("requestHandlers has been set to None intentionally in {0}".format(name))

        isCallable = hasattr(requestHandlers, "__call__")
        if not isCallable:
            try:
                requestHandlers = dict(requestHandlers)
            except (ValueError, TypeError):
                try:
                    methods = dict(requestHandlers.items())
                except (ValueError, TypeError, AttributeError):
                    mcls._raiseNoValidRequestHandlers(name)
        else:
            defaultHandler = requestHandlers
            requestHandlers = collections.defaultdict(lambda: defaultHandler)
            dct["requestHandlers"] = requestHandlers


        for val in requestHandlers.viewvalues():
            if not hasattr(val, "__call__"):
                raise TypeError("All values in requestHandlers dict must be callable.")

        return abc.ABCMeta.__new__(mcls, name, bases, dct)

class Node(object):
    """
    Baseclass for a *tree node* in the site tree. Use this to create your own
    site tree plugins. It is highly recommended that you have a look at the
    existing plugins implementation.

    *site* must be a :class:`~PyXWF.Site` instance. *parent* must be a
    :class:`~PyXWF.Nodes.Node` instance (or :data:`None` for the root) which
    is the parent of the node which is to be created.

    *node* may be either a :class:`lxml.etree._Element` instance or
    :data:`None`. This changes the behaviour of the node initialization as
    follows:

    *   If *node* is **not** :data:`None`:

        The attributes ``@id`` (default :data:`None`), ``@name`` (default
        ``""``) and ``@template`` (default :data:`None`) are stored in their
        respective private object attribute.

        The path of the node is calculated by taking the parents path (if any)
        and appending a ``/`` and the nodes name to it.

    *   Otherwise: The private id, name, template and path attributes are
        initialized to :data:`None`.

    To create a node class you have to use the :class:`PyXWF.Registry.NodeMeta`
    class, which requires some attributes::

        class CoolNode(Node):
            __metaclass__ = Registry.NodeMeta

            # xml namespace
            namespace = "hettp://example.com/cool-node"

            # list of xml local-names to register for in the above namespace
            # if you don't want to do something fancy, just use ["node"]
            names = ["node"]

            # your methods go here, like so:
            def doGet(self, ctx):
                return self.arbitaryDocument

            # define which methods handle which HTTP request method
            requestHandlers = {
                "GET": doGet
            }

            # if you have one method to rule them all you can also do:
            requestHandlers = doGet

            # if you want to deny instanciation of your class (not useful):
            requestHandlers = None

            # if you want to return a MethodNotAllowed on each request:
            requestHandlers = {}

    Note that this is not all you need to create a node. For a complete tutorial
    on how to create nodes see :ref:`<create-a-plugin-node>`.
    """
    __metaclass__ = NodeMeta

    _navTitleWithNoneType = Types.DefaultForNone(None, Types.Typecasts.unicode)

    def __init__(self, site, parent, node, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.Parent = parent
        self.Site = site
        self._id = None
        self._name = None
        self._template = None
        self._path = None

        if node is not None:
            self.loadFromNode(node)

    def loadFromNode(self, node):
        self.ID = node.get("id")
        self._name = node.get("name", "")
        self._template = node.get("template", None)
        if self.Parent and self.Parent.Path:
            parentPath = self.Parent.Path
        else:
            parentPath = ""
        self._path = parentPath + self._name

    def iterUpwards(self, stopAt=None):
        """
        Return an iterable which yields the nodes walking tree upwards
        (following the :attr:`.parent` attribute) until that attribute is
        either :data:`None` or *stopAt* (both are not yielded).
        """

        node = self
        while node is not None and node is not stopAt:
            yield node
            node = node.Parent

    def handle(self, ctx):
        """
        Handle the request represented by the :class:`~PyXWF.Context.Context`
        instance *ctx*.

        This tries to look up the value of the
        :attr:`~PyXWF.Context.Context.Method` used for the request in the
        :attr:`.requestHandlers` dict. If that fails,
        :class:`~PyXWF.Errors.MethodNotAllowed` is raised. Otherwise, the result
        (which must be a callable) is called with *ctx* is the parameter and the
        result of the call is returned.
        """
        try:
            handler = self.requestHandlers[ctx.Method]
        except KeyError:
            raise Errors.MethodNotAllowed(self.requestHandlers.viewkeys())
        except TypeError:
            return self.requestHandlers(ctx)
        return handler(self, ctx)

    def resolvePath(self, ctx, relPath):
        """
        Resolve the path *relPath* relative to the current node using the
        request :class:`~PyXWF.Context.Context` *ctx*. In the default
        implementation, this checks whether *relPath* is the empty string and
        returns the node. If *relPath* is not the empty string,
        :class:`~PyXWF.Errors.NotFound` is raised.

        Subclasses override this method to add children to the path, see
        :class:`~PyXWF.Nodes.DirectoryResolutionBehaviour` for an example.
        """
        if relPath == "":
            return self
        raise Errors.NotFound(resourceName=ctx.Path)

    def getContentType(self, ctx):
        """
        Return the MIME type of the document returned by this node in the given
        request context *ctx*.
        """
        return ContentTypes.xhtml

    @property
    def Template(self):
        """
        Return the name of the template which is to be used to render the
        document. This is either the value of the ``@template`` attribute of the
        XML node which initialized this tree node, or the parents
        :attr:`.Template` value.

        This is :data:`None` if ``@template`` was not set and the node has no
        parent or that parent itself has a :data:`None` value for
        :attr:`.Template`.
        """
        template = self._template
        if template is None and self.Parent is not None:
            template = self.Parent.Template
        return template

    @Template.setter
    def Template(self, value):
        self._template = value

    @property
    def Name(self):
        """
        Path segment name of this node.
        """
        return self._name

    @property
    def Path(self):
        """
        The full path from the application root to this node.

        .. warning::
            Do not assume that, while this property is writable, changing it
            will make the node available at a given path. Path resolution takes
            place along the chain of nodes from the tree root downwards. So this
            property is just informational and will be initialized correctly by
            the node itself or the parent node respectively (if the parent node
            does something fancy)
        """
        return self._path

    @Path.setter
    def Path(self, value):
        """
        Change the path under which the node assumes it's available.
        """

    @property
    def ID(self):
        """
        Unique string ID of the node (initialized from the ``@id`` attribute of
        the original XML node). This can be used as an argument to
        :meth:`~PyXWF.Site.getNode` to retrieve the node.
        """
        return self._id

    @ID.setter
    def ID(self, value):
        value = str(value) if value is not None else None
        if self._id == value:
            return
        if self._id is not None:
            del self.Site.nodes[self._id]
        self._id = value
        if self._id is not None:
            self.Site.registerNodeID(self._id, self)


    @abc.abstractmethod
    def getNavigationInfo(self, ctx):
        """
        This must be implemented by subclasses which are to be mounted in the
        tree and return a valid :class:`PyXWF.Navigation.Info` instance.
        """

    requestHandlers = {}


class DirectoryResolutionBehaviour(object):
    """
    Mixin to make a node behave like a directory, regarding the working of
    *resolvePath*. For this, the method *_getChildNode* must be implemented.

    If the path points to the node using this behaviour and is missing a
    trailing /, a redirect is issued. Otherwise, the next path segment is taken
    (i.e. the part *behind* the / which follows the path to the current node but
    *in front of* the next /, if any) and a lookup using *_getChildNode* is
    attempted.

    .. warning::
        When using this mixin, make sure you mix it into your inheritance
        hierarchy *before* the :class:`~.Node` class! Otherwise the mixin will
        not work. Example::

            # good
            class AwesomeDirectory(DirectoryResolutionBehaviour, Node):
                "stuff goes here"

            # bad!
            class AwesomeDirectory(Node, DirectoryResolutionBehaviour):
                "stuff goes here"

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _getChildNode(self, key):
        """
        Return the node at the path segment *key*. *key* will be the empty
        string, if no next path segment is given in the path.

        Returns ``None`` if there is no Node at the given *key*.

        Raise a HTTPRedirect error if the resource can be found under a
        different location. Set *local* attribute of that exception to any value
        and pass only the new key to *location* to automatically generate
        correct paths.
        """

    @property
    def Path(self):
        path = super(DirectoryResolutionBehaviour, self).Path
        if not path or path[-1] != "/":
            path += "/"
        return path

    def resolvePath(self, ctx, relPath):
        fullPath = ctx.Path
        if fullPath[-1:] != "/" and len(relPath) == 0 and len(fullPath) > 0:
            raise Errors.Found(location=fullPath+"/")
        try:
            pathHere, relPath = relPath.split("/", 1)
        except ValueError:
            pathHere = relPath
            relPath = ""
        try:
            node = self._getChildNode(pathHere)
        except Errors.HTTPRedirection as err:
            if hasattr(err, "local"):
                trailPathLen = len(relPath)+len(pathHere)+1
                err.location = fullPath[:-(trailPathLen)] + err.location + relPath
            else:
                raise
        if node is None:
            raise Errors.NotFound()
        if node is not self:
            return node.resolvePath(ctx, relPath)
        else:
            return node
