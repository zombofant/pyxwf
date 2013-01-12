#########################
``sitemap.xml`` reference
#########################

The ``sitemap.xml`` document is the most important XML document of your
entire site. It is important to know the various tweaks of the document
to optimize your site and being able to customize it to your wishes.

This document gives a detailed description on the various options
the ``sitemap.xml`` offers. Before you go on reading in the subsections,
you should understand the basic struture of a ``sitemap.xml`` file.

.. toctree::
    :maxdepth: 2

***********************
Basic sitemap structure
***********************

To save us typing, we'll refer to nodes in the ``site:`` namespace
(``http://pyxwf.zombofant.net/xmlns/site``) without prefix, just like
in the following basic XML tree of a sitemap::

    <?xml version='1.0' encoding='utf-8' ?>
    <site   xmlns="http://pyxwf.zombofant.net/xmlns/site">
        <meta />
        <plugins />
        <tweaks />
        <tree />
        <crumbs />
    </site>

While the order of the elements of the ``<site />`` node is not
enforced, it is reasonable to keep it that way in the XML file. This
is the very same order in which the nodes are processed by the
framework, so it's quite a good way to reflect in which direction
interaction between the nodes can happen.

For example, you usually cannot reference something which is within the
tree from a node inside of ``<tweaks />``. Also please note that
this sitemap structure is **not valid**. It cannot be, but we'll sort
that out in the tree section later.

****************************
``<meta />`` — Site metadata
****************************

The ``<meta />`` node contains metadata about the site. It can
contain several elements. If you don't want to read the whole reference,
just skip below the itemization and we'll talk about which elements are
the most important. You can then go back and read up on their usage.

*   ``<title />`` (exactly one)

    **Attributes:** None

    **Text content:** Title of the website (for use in templates)

    This specifies the title of the website. It'll be available as a
    template parameter in the current nodes template upon transformation
    as ``$site_title``.

*   ``<root />`` (one or zero, if *rootpath* is set by other means)

    **Attributes:** None

    **Text content:** Filesystem path to the data files

    The path given by this node is used as a root path for any data
    files used by the website. This includes referenced templates,
    XML source files, static content source files (such as those
    referenced by ``page:node/@src`` attributes) and so on.

    This can also be set by different means. If the node is omitted,
    the current working directory which was set when the sitemap was
    read is used.

*   ``<urlroot />`` (one or zero, if *urlroot* is set by other means)

    **Attributes:** None

    **Text content:** URL path component

    The path component given is assumed to be the static prefix after
    the *host*-part of any URL pointing to the application. Thus,
    assuming that your host is called ``example.com``, if the
    application is deployed at ``http://example.com/my-pyxwf-app/``,
    the *urlroot* would have to be ``/my-pyxwf-app/``.

    Note that this can also be passed by the WSGI script (or whatever
    applies to your web backend) upon construction of the
    :class:`~PyXWF.Site.Site` object.

*   ``<author />`` (zero or more)

    **Attributes:**

    :@id: *unique id string* — (required)
    :@href: *url* — (optional) Home page or descriptive website
    :@email: *email address* — (optional) e-mail address of the author

    **Text content:** Full name (or display name)

    Just like authors can be declared per-document, a predefined set of
    authors can be setup in the sitemap itself. This reduced code
    duplication. In documents, these authors can be referred to by
    referring to the value in the ``@id`` attribute of the sitemap
    authors.

    The display of authors depends on the template used. The user is
    responsible for transforming ``<py:author />`` nodes into XHTML
    (or whichever output format is used).

*   ``<license />`` (zero or one)

    **Attributes:**

    :@name: *string* — Short name for the license
    :@href: *url* — (optional) URL to a descriptive website of the license
    :@img-href: *url* — (optional) URL to a descriptive image of the license

    **Text content:** Long description of the license

    This is the default license associated with the websites content.
    If the document which is to be rendered has no license specified,
    this, if available, will be used instead.

If you followed the tutorial for setting up a PyXWF instance, you
won't have to deal with roots and urlroots. For a basic website, you'll
only use ``<title />`` and perhaps ``<license />``. If you're going to
add a blog, you probably also need ``<author />``. These are quite
straightforward to use, so not much to worry about.

*********************************
``<plugins />`` — Loading plugins
*********************************

As mentioned elsewhere, PyXWF is so modular, that even the most basic
things are refactored into plugins, of which only one or two are loaded
by default. You'll have to load the rest. This allows you to optimize
the resource use of PyXWF down to the absolute minimum.

The plugins which are most often used are probably the Directory and
Page plugins. To load a plugin, you have to add a ``<p />`` node to
the ``<plugins />`` node, like this::

    <p>PyXWF.Nodes.Page</p>
    <p>PyXWF.Nodes.Directory</p>
    <p>PyXWF.Nodes.Redirect</p>

There are more, check out the docs for a full list. PyXWF will load
these plugins after it has loaded the metadata. Please refer to the
section about reloading the sitemap to read on some implications.

*********************************************
``<tweaks />`` — supply further configuration
*********************************************

PyXWF offers several possibilities to tweak its behaviour, and most
plugins come with even more. Here, only the so called CoreTweaks,
offered by a plugins which is loaded by default, are discussed. These
are nodes which can be added to the ``<tweaks />`` node. None of this
is required.

Each subsection of this section represents a node which can be used
inside ``<tweaks />``. Inside these sections, we'll go into details
of the attributes and subnodes this node can take. Each of these nodes
can occur multiple times. Each time, the previous values will be
overwritten by those which have been set by previous nodes.

``<performance />`` — settings which affect performance
=======================================================

*   ``@cache-limit``

    Requires an integer value greater than or equal to zero. Set the
    maximum count of objects to be kept in the cache between two
    requests.

    If set to a non-zero value, the entries whose access timestamp
    (which is updated each time the object is requested from the cache)
    is most in the past, will be purged from the cache until the cache
    contains an element count less or equal to this limit.

    If set to zero, the cache will never be purged. Note that this can
    lead to exorbitant memory usage.

    The default is a value of zero.

*   ``@pretty-print``

    Requires a boolean value (``true`` or ``false``). If this is set
    to true, the XML output sent to the user will be pretty-printed.
    This may ease debugging, but costs a lot of performance and
    memory, and is thus disabled by default.

    If you are serving XHTML (the default), you'll also notice that this
    can affect spacing between elements.

    The default is false.

*   ``@client-cache``

    Requires a boolean value. If this is set to false, PyXWF makes clear
    to the user agent in its response, that the response MUST NOT be
    cached. Note that this won't prevent some user agents to cache the
    response nevertheless, but it still makes debugging a bit easier.

    The default is false.

``<compatibility />`` — to deal with bad user agents
====================================================

*   ``@html4-transform``

    Requires a path to an XSL document. The transformation will be
    applied whenever PyXWF detects that the user agent cannot deal
    with HTML5 properly.

    PyXWF comes with a default html4 transform which is also the default
    value. It can be looked at in the PyXWF directory,
    ``data/xsl/tohtml4.xsl``.

*   ``@disable-xhtml``

    Requires a boolean value. If set to true, XHTML responses are
    disabled altogether. PyXWF will always convert the XHTML document
    to plain HTML, independently of the user agent.

    If this is set to false, PyXWF will use a mix of
    HTTP Content Negotiation and smart guesses about the user agent to
    figure out whether to serve XHTML or HTML and do the right thing.

    The default is false.

*   ``@remove-xhtml-prefixes``

    Requires a boolean value. If set to true, PyXWF will remove the
    XHTML prefixes for all user agents of which it does not know that
    they support it properly.

    You should enable this option if you're experiencing problems with
    JavaScript, especially in Firefox.

    The default is false.

``<formatting />`` — text/date formatting options
=================================================

*   ``@short-date-format``

    A ``strftime`` compatible format string to use for every place where
    a datetime value is to be converted into a short string.

    The default is to use the locale-specific ``%c``.

*   ``@long-date-format``

    A ``strftime`` compatible format string to use for every place where
    a datetime value is to be converted into a extensive string.

    The default is to use the locale-specific ``%C``.

*   ``@date-format``

    A ``strftime`` compatible format string for all date formatting
    taking place in PyXWF or plugins. This is a meta-setting which
    sets both ``@long-date-format`` and ``@short-date-format`` and has
    no default value.

``<templates />`` — default XSL templates
=========================================

*   ``@default``

    Requires a path to an XSL document. This is the template to use
    if the node which is to be served has no template specified.

``<mimemap />`` — declare file extensions
=========================================

*   ``<mm />`` (zero or more)

    **Attributes:**

    :ext: *file extension* — (required) The file extension to match
    :type: *mime type* — (required) MIME type to assign to the extension

    **Text content:** None

    Assigns the mime type ``@type`` to the file extension ``@ext``.
    This is useful to define custom file extensions and can save you
    some typing for ``@type`` attributes on some nodes.

``<html-transform />`` — further custom templates
=================================================

This is the only node which can be there multiple times and won't
override previous settings. Instead, each occurence adds another XSL
template to the transform chain. These templates will be executed after
the XHTML document has been generated and after the final PyXWF
transform has been applied.

*   ``@transform``

    Requires a path to an XSL document.


*********************************************
``<:tree />`` — Creating the actual site tree
*********************************************

Now we come to talk about the tree nodes. PyXWF requires exactly one
node which has the localname ``tree`` in the sitemap. This will be used
as the root node for the sitemap and this is where the requests are
dispatched into. The path is resolved down the node tree until either
the matching node is found or an error gets raised.

Which elements can be used here really depends on your plugins.
Usually, you use a ``<dir:tree />`` node.

***********************************************
``<crumbs />`` — Snippets and generated content
***********************************************

Crumbs, or widgets, whatever you like to call them, are quite essential
to get a good-looking and consistent website in a wink.

PyXWF comes with several plugins featuring crumbs, most notably the
NestedMenu and Breadcrumb plugins, which offer a nested tree of
``<h:ul />`` elements representing your sitemap (or a part thereof) and
a chain of ``<h:a />`` elements giving the well-known breadcrumbs
respectively.

*********************
Reloading the sitemap
*********************

Finally, we have to talk about some things which are important when
using PyXWF with a non-CGI server. You'll see that PyXWF will reload
the sitemap every time it gets changed.

This is convenient. It'll purge the complete cache, drop all resources
it has loaded so far, and start from scratch. Nearly. The only thing
you *cannot* unload by removing it from the sitemap and have PyXWF
reload it, are plugins. Those are imported as Python modules and those
will not become reloaded with the sitemap.

Even with Pythons :func:`reload` function it is a highly non-trival task
to get the order and dependencies for reloading right, so we decided to
leave it up to the admin to reload the whole server process if changes
to the code or the used plugins are made.

You can, however, load additional plugins by just adding them to the
sitemap.
