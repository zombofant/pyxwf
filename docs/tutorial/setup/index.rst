****************
Setting up PyXWF
****************

PyXWF currently requires a dedicated webserver with
`WSGI <http://www.python.org/dev/peps/pep-3333/>`_ support. Many widely-used
webservers (at least Apache and lighttpd) support WSGI using a module.

In addition to the python code, you'll have a repository with content, which is
where you put all the data which belongs to the site. We call this the
*data directory*, while the directory where PyXWF resides is the
*PyXWF directory*.

Creating the sitemap and initial data
=====================================

All those files referenced in this section are available in an example form in
the PyXWF repository, in the subdirectory ``misc/example``. You may use these
as a reference to build your own customized website.

PyXWF requires at least one file, the so called ``sitemap.xml`` (although you
can choose a different name). This is an XML file where the whole configuration
for PyXWF goes. It usually resides in the root of the *data directory*.

This is how a bare ``sitemap.xml`` looks (it won't work)::

    <?xml version="1.0" encoding="utf-8" ?>
    <site   xmlns="http://pyxwf.zombofant.net/xmlns/site"
            xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
            xmlns:dir="http://pyxwf.zombofant.net/xmlns/nodes/directory">
        <meta>
            <title>My fancy PyXWF site</title>
        </meta>
        <plugins>
            <p>PyXWF.Nodes.Directory</p>
        </plugins>
        <tweaks />
        <dir:tree
                id="treeRoot"
                template="templates/default.xsl">
        </dir:tree>
        <crumbs />
    </site>

We'll use this as a basement for our walk through the configuration process.
Before we go on, I'll leave a few words on how we at PyXWF think about XML
namespaces, as what we're doing here may seem a bit weird to you if you know
XML (if you don't, you probably should read up on XML anyways, cause most of
PyXWF happens in XML and Python).

PyXWF is really modular, as you might guess from the snippet above, even the
most basic elements like a directory in a site structure are plugins. To keep
the plugins separated from each other in the sitemap XML, each plugin has to
use its own XML namespace.

This brings you to a dilemma when it comes to find the root of the tree in the
sitemap XML: because you _cannot_ know its namespace. Someone could decide to
put a Transform node at the root or just a single page or a remote redirect.

So we have to scan through the whole ``<site />`` node and find a child with the
XML local-name *tree*. This is the only place in PyXWF itself where the
local-name of a node matters.

The ``@template`` attribute on the ``<dir:tree />`` node by the way states the
default template used to render web pages. We'll talk about templates later,
namely when we create the file referenced there.

Adding a home page
------------------

As mentioned previously, this sitemap will not work in PyXWF. You'll recieve
an error message which tells you that the ``dir:tree`` node needs an index
node.

So let's add one::

        <dir:tree
                id="treeRoot"
                template="templates/default.xsl">
            <page:node  name="" id="home"
                src="home.xml"
                type="application/x-pywebxml" />
        </dir:tree>

This won't work on it's own, we have to add two other things. First, the
``page`` namespace prefix needs to be resolved. We do that by adding the
declaration to the ``<site />`` node::

    <site   xmlns="http://pyxwf.zombofant.net/xmlns/site"
            xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
            xmlns:dir="http://pyxwf.zombofant.net/xmlns/nodes/directory"
            xmlns:page="http://pyxwf.zombofant.net/xmlns/nodes/page">

And we also need to load the plugin by adding another ``<p />`` tag::

        <plugins>
            <p>PyXWF.Nodes.Directory</p>
            <p>PyXWF.Nodes.Page</p>
        </plugins>

Now let's add source file for the home page. As you might guess, the
``@src`` attribute of a ``<page:node />`` references the file in which the
node looks for the source of the document to display. All paths are relative
to the *data directory*. So we create a ``home.xml`` file, which has to look
like this to satisfy the ``application/x-pywebxml`` content type set in
``@type``::

    <?xml version="1.0" encoding="utf-8" ?>
    <page   xmlns="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
            xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml">
        <meta>
            <title>Home page</title>
        </meta>
        <body xmlns="http://www.w3.org/1999/xhtml">
            <header>
                <!-- note that hX tags automatically get transformed to hX+1 tags
                     according to the environment where they're used. -->
                <h1>Welcome to my website!</h1>
            </header>
            <p>I just set up PyXWF and want to play around.</p>
        </body>
    </page>

The root element of a PyWebXML document must be a ``<py:page />`` node in
the namespace given above. We usually choose the ``py:`` prefix to reference
this namespace (for more elements and attributes which can be used in that
namespace have a look at the respective documentation). For more information
about PyWebXML documents see :ref:`<py-namespace>`. The only thing you need
to know now is that you can use arbitary XHTML (and anything you can use in
XHTML) inside the ``<h:body />`` element. It will be displayed on page, a correct
template presumed.

Adding a template
-----------------

Templates in PyXWF are XSL transformations. If you don't know anything about
these, you're probably lost. We cannot help you there, you maybe should get some
resources on these.

I won't paste a whole default template here. Instead, i'll describe in short
what the outermost template must do to create a proper website.

*   The input of the transformation is always a valid ``py:page`` tree.
*   The output of the transformation must be a valid ``py:page`` tree.
*   The ``h:body`` of the ``py:page`` tree should contain the whole body which
    should appear in the HTML output.
*   The ``py:meta`` element should contain a ``py:title`` element which will map
    to the HTML title.
*   The ``py:meta`` element can also contain as many ``py:link`` and
    ``h:meta`` elements neccessary to describe your page. Please see the
    ``py:link`` documentation on how to include javascript files.


Setting up WSGI
===============

As mentioned before, PyXWF connects to the Web using WSGI. Here are the
neccessary configuration steps to get it to work.

Create the WSGI script
----------------------

You may want to have a look at ``misc/examples/pyxwf.py`` from the PyXWF
repository to see how a WSGI script might look. Most important is to set up the
path to the *data directory* properly, and make sure that PyXWF is in your
python path.

``mod_wsgi`` with Apache
------------------------

We are using a configuration similar to this one for zombofant.net::

    WSGIScriptAlias / /path/to/zombofant/data/pyxwf.py

    # access to static files via Apache, PyXWF won't do that
    Alias /css /path/to/zombofant/data/css
    Alias /img /path/to/zombofant/data/img

Actually, thats all you need. Read up on
`WSGI configuration <https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide>`_
to see how to adapt this to your needs if it doesn't work out of the box.

From there on you should be able to access PyXWF through your webbrowser.
Congratulations!
