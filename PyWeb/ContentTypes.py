# encoding=utf-8
"""
Contains only a few content type declarations. These may be used around the
application and it's better to have them in one place.

It also provides normalization functionality for content types which are often
used interchangably. Returns the “right” content type.
"""

xhtml = "application/xhtml+xml"
html = "text/html"
plainText = "text/plain"
Atom = "application/atom+xml"
PyWebXML = "application/x-pyweb-xml"

normalization = {
    "application/xhtml+xml": xhtml,
    "text/xhtml": xhtml,
    "application/xhtml": xhtml,
    "text/html": html,
}
