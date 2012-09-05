import abc, collections

import PyXWF.utils as utils
import PyXWF.Errors as Errors
import PyXWF.Types as Types
import PyXWF.ContentTypes as ContentTypes

class NodeMeta(abc.ABCMeta):
    """
    Metaclass which deals with enforcing the existance of the *request_handlers*
    attribute and its contents.

    .. note::
        You don't use this metaclass usually. To create a complete node class,
        you need the :class:`PyXWF.Registry.NodeMeta` metaclass.
    """

    @classmethod
    def _raise_no_valid_request_handlers(mcls, name):
        raise TypeError("{0} requires request_handlers as dict (or dict-compatible) or callable".format(name))

    def __new__(mcls, name, bases, dct):
        try:
            request_handlers = dct["request_handlers"]
        except KeyError:
            for base in bases:
                try:
                    request_handlers = base.request_handlers
                    break;
                except AttributeError:
                    pass
            else:
                mcls._raise_no_valid_request_handlers(name)
        if request_handlers is None:
            raise TypeError("request_handlers has been set to None intentionally in {0}".format(name))

        is_callable = hasattr(request_handlers, "__call__")
        if not is_callable:
            try:
                request_handlers = dict(request_handlers)
            except (ValueError, TypeError):
                try:
                    methods = dict(request_handlers.items())
                except (ValueError, TypeError, AttributeError):
                    mcls._raise_no_valid_request_handlers(name)
        else:
            default_handler = request_handlers
            request_handlers = collections.defaultdict(lambda: default_handler)
            dct["request_handlers"] = request_handlers


        for val in request_handlers.viewvalues():
            if not hasattr(val, "__call__"):
                raise TypeError("All values in request_handlers dict must be callable.")

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
            def do_GET(self, ctx):
                return self.arbitrary_document

            # define which methods handle which HTTP request method
            request_handlers = {
                "GET": do_GET
            }

            # if you have one method to rule them all you can also do:
            request_handlers = do_GET

            # if you want to deny instanciation of your class (not useful):
            request_handlers = None

            # if you want to return a MethodNotAllowed on each request:
            request_handlers = {}

    Note that this is not all you need to create a node. For a complete tutorial
    on how to create nodes see :ref:`<create-a-plugin-node>`.
    """
    __metaclass__ = NodeMeta

    _navtitle_with_none_type = Types.DefaultForNone(None, Types.Typecasts.unicode)

    def __init__(self, site, parent, node, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.Parent = parent
        self.Site = site
        self._id = None
        self._name = None
        self._template = None
        self._path = None

        if node is not None:
            self.load_from_node(node)

    def load_from_node(self, node):
        self.ID = node.get("id")
        self._name = node.get("name", "")
        self._template = node.get("template", None)
        if self.Parent and self.Parent.Path:
            parent_path = self.Parent.Path
        else:
            parent_path = ""
        self._path = parent_path + self._name

    def iter_upwards(self, stop_at=None):
        """
        Return an iterable which yields the nodes walking tree upwards
        (following the :attr:`.parent` attribute) until that attribute is
        either :data:`None` or *stop_at* (both are not yielded).
        """

        node = self
        while node is not None and node is not stop_at:
            yield node
            node = node.Parent

    def handle(self, ctx):
        """
        Handle the request represented by the :class:`~PyXWF.Context.Context`
        instance *ctx*.

        This tries to look up the value of the
        :attr:`~PyXWF.Context.Context.Method` used for the request in the
        :attr:`.request_handlers` dict. If that fails,
        :class:`~PyXWF.Errors.MethodNotAllowed` is raised. Otherwise, the result
        (which must be a callable) is called with *ctx* is the parameter and the
        result of the call is returned.
        """
        try:
            handler = self.request_handlers[ctx.Method]
        except KeyError:
            raise Errors.MethodNotAllowed(self.request_handlers.viewkeys())
        except TypeError:
            return self.request_handlers(ctx)
        return handler(self, ctx)

    def resolve_path(self, ctx, relpath):
        """
        Resolve the path *relpath* relative to the current node using the
        request :class:`~PyXWF.Context.Context` *ctx*. In the default
        implementation, this checks whether *relpath* is the empty string and
        returns the node. If *relpath* is not the empty string,
        :class:`~PyXWF.Errors.NotFound` is raised.

        Subclasses override this method to add children to the path, see
        :class:`~PyXWF.Nodes.DirectoryResolutionBehaviour` for an example.
        """
        if relpath == "":
            return self
        raise Errors.NotFound(resource_name=ctx.Path)

    def get_content_type(self, ctx):
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
        :meth:`~PyXWF.Site.get_node` to retrieve the node.
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
            self.Site.register_node_id(self._id, self)


    @abc.abstractmethod
    def get_navigation_info(self, ctx):
        """
        This must be implemented by subclasses which are to be mounted in the
        tree and return a valid :class:`PyXWF.Navigation.Info` instance.
        """

    request_handlers = {}


class DirectoryResolutionBehaviour(object):
    """
    Mixin to make a node behave like a directory, regarding the working of
    *resolve_path*. For this, the method *_get_child* must be implemented.

    If the path points to the node using this behaviour and is missing a
    trailing /, a redirect is issued. Otherwise, the next path segment is taken
    (i.e. the part *behind* the / which follows the path to the current node but
    *in front of* the next /, if any) and a lookup using *_get_child* is
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
    def _get_child(self, key):
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

    def resolve_path(self, ctx, relpath):
        fullpath = ctx.Path
        if fullpath[-1:] != "/" and len(relpath) == 0 and len(fullpath) > 0:
            raise Errors.Found(location=fullpath+"/")
        try:
            pathhere, relpath = relpath.split("/", 1)
        except ValueError:
            pathhere = relpath
            relpath = ""
        try:
            node = self._get_child(pathhere)
        except Errors.HTTPRedirection as err:
            if hasattr(err, "local"):
                trail_path_len = len(relpath)+len(pathhere)+1
                err.location = fullpath[:-(trail_path_len)] + err.location + relpath
            else:
                raise
        if node is None:
            raise Errors.NotFound()
        if node is not self:
            return node.resolve_path(ctx, relpath)
        else:
            return node
