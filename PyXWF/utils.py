# encoding=utf-8
# File name: utils.py
# This file is part of: pyxwf
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyxwf please e-mail one of the
# authors named in the AUTHORS file.
########################################################################

import abc, os, re, logging
from datetime import datetime

import lxml.etree as ET

# http://plumberjack.blogspot.de/2010/10/supporting-alternative-formatting.html
class BraceMessage(object):
    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)

_F = BraceMessage

class NoInstance(type):
    def _not_instanciable(*args):
        raise TypeError("Cannot instanciate {0}".format(cls.__name__))

    def __new__(mcls, name, bases, dct):
        dct["__new__"] = mcls._not_instanciable
        return super(NoInstance, mcls).__new__(mcls, name, bases, dct)

def split_tag(tag):
    """
    Split an ElementTree tag into its namespace and XML local-name and return
    these as a tuple ``(namespace, localname)``. If the tag has no namespace
    associated, :data:`None` is returned for *namespace*.
    """
    assert(isinstance(tag, basestring))
    if len(tag) == 0:
        return None, ""
    if tag[0] == "{":
        cbrace = tag.find("}")
        ns = tag[1:cbrace]
        name = tag[cbrace+1:]
        return ns, name
    else:
        return None, tag

def add_class(node, cls):
    """
    Take the ``@class`` attribute of *node*, split it at spaces, put it into a
    :class:`set`, add *cls* to the set and re-join the set with spaces.
    """
    classes = set(node.get("class", "").split())
    classes.add(cls)
    node.set("class", " ".join(classes))


def file_last_modified(fileref, float_times=False):
    """
    If *fileref* is a file name or a file like with associated fileno which
    points to an actual file, return the date of last modification
    stored in the filesystem, :data:`None` otherwise.

    By default, the times are truncated to full seconds. If you need the
    floating point part of the times (if supported by the platform), pass
    ``True`` to *float_times*.
    """
    try:
        if isinstance(fileref, basestring):
            st = os.stat(fileref)
        else:
            fno = fileref.fileno()
            if fno >= 0:
                st = os.fstat(fno)
            else:
                return None
    except (OSError, AttributeError):
        return None
    if float_times:
        mtime = st.st_mtime
    else:
        mtime = int(st.st_mtime)
    return datetime.utcfromtimestamp(mtime)

def unicode2xpathstr(value):
    return '"'+unicode(value).replace("\"", "\\\"")+'"'

def parse_iso_date(s):
    """
    Parse a date like returned with :meth:`~datetime.datetime.isoformat`, but
    with a trailing `Z` to indicate the UTC timezone.
    """
    if s is None:
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")

def XHTMLToHTML(tree):
    """
    Converts the given ETree *tree* from XHTML to HTML *in-place*. Raises
    :class:`ValueError` if a non-XHTML namespace is encountered.
    """
    import PyXWF.Namespaces as NS
    xhtml_ns = str(NS.XHTML)
    for item in tree.iter():
        if not isinstance(item.tag, basestring):
            continue
        ns, name = split_tag(item.tag)
        if ns != xhtml_ns:
            logging.debug("offending element: {0}".format(ET.tostring(item)))
            raise ValueError("tree contains non-xhtml elements: {0}:{1}".format(ns, name))
        item.tag = name
    ET.cleanup_namespaces(tree)

mobile_useragent_re = re.compile("(\sMobile\s|\sMobile/[0-9a-fA-F]+)")

useragent_regexes = [
    ("googlebot", re.compile("Googlebot/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("googlebot", re.compile("Googlebot-Image/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("bingbot", re.compile("bingbot/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("ahrefsbot", re.compile("AhrefsBot/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("yandexbot", re.compile("YandexBot/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("yahoo-slurp", re.compile("Yahoo! Slurp/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("yahoo-slurp", re.compile("Yahoo! Slurp")),
    ("speedy-spider", re.compile("Speedy Spider")),
    ("sistrix-crawler", re.compile("SISTRIX Crawler")),
    ("msnbot", re.compile("msnbot/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("msnbot", re.compile("msnbot-media/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("konqueror", re.compile("Konqueror/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("chrome", re.compile("Chrome/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("ie", re.compile("MSIE ([0-9]+(\.[0-9]+)?)")),
    ("firefox", re.compile("Firefox/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("firefox", re.compile("Gecko/[0-9]+\s+Firefox[0-9]+")),
    ("firefox", re.compile("Minefield/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("firefox", re.compile("Iceape/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("firefox", re.compile("Iceweasel/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("seamonkey", re.compile("SeaMonkey/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("safari", re.compile("Safari/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("opera", re.compile("Opera/([0-9.]+).*Version/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("opera", re.compile("Opera/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("lynx", re.compile("Lynx/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("links", re.compile("Links ")),
    ("w3m", re.compile("w3m/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("wget", re.compile("[Ww]get/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("rotfuchs", re.compile("Gecko Rotfuchs")),
    ("epiphany", re.compile("Epiphany/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("rssowl", re.compile("RSSOwl/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("askbot", re.compile("Ask Jeeves")),
    ("exabot", re.compile("Exabot/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("seekbot", re.compile("Seekbot/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("libwww-perl", re.compile("libwww-perl/(?P<version>[0-9]+(\.[0-9]+)?)")),
    ("blank", re.compile("^\s*-\s*$"))
]

useragent_classes = {
    "googlebot": "indexer",
    "bingbot": "indexer",
    "yahoo-slurp": "indexer",
    "msnbot": "indexer",
    "speedy-spider": "crawler",
    "sistrix-crawler": "crawler",
    "wget": "crawler",
    "firefox": "browser",
    "seamonkey": "browser",
    "safari": "browser",
    "opera": "browser",
    "links": "browser",
    "lynx": "browser",
    "rotfuchs": "browser",
    "chrome": "browser",
    "ie": "browser",
    "w3m": "browser",
    "konqueror": "browser",
    "yandexbot": "indexer",
    "ahrefsbot": "crawler",
    "epiphany": "browser",
    "askbot": "indexer",
    "rssowl": "feedreader",
    "exabot": "indexer",
    "seekbot": "indexer",
}

def guess_useragent(headerval):
    """
    Return a tuple ``(useragent, version)``, where *useragent* is one of:

    * ``ie`` for Internet Explorer™
    * ``firefox`` for firefox
    * ``mozilla`` for mozilla
    * ``opera`` for opera
    * ``safari`` for safari
    * ``links`` for links
    * ``lynx`` for lynx
    * ``wget`` for wget
    * ``chrome`` for chrome
    * ``yahoo-slurp`` for yahoo slurp bot
    * ``konqueror`` for konqueror
    * ``googlebot`` for googlebot
    * None for each unknown user agent

    *version* will be either the version number of the user agent or None if the
    version could not be determined reliably. The version number is represented
    as a floating point value.
    """
    for agentname, regex in useragent_regexes:
        m = regex.search(headerval)
        if m:
            groups = m.groupdict()
            if len(groups) > 0:
                version = float(groups["version"])
            else:
                version = None
            return agentname, version
    else:
        return (None, None)

def classify_useragent(uaname):
    return useragent_classes.get(uaname, None)

def is_mobile_useragent(headerval):
    return mobile_useragent_re.search(headerval) is not None

def chunk_string(s, chunk_size=1024):
    off = 0
    while True:
        yield s[off:off+chunk_size]
        off += chunk_size
        if off >= len(s):
            return
try:
    import threading
except ImportError as err:
    logging.warning(_F("Could not import threading: {0}", err))
    logging.warning("Will fallback to dummy_threading; expect promlems")
    import dummy_threading as threading

try:
    import blist
    try:
        blist.__version__
    except AttributeError:
        # blist doesn't have version tag
        blist.__version__ = "native"
except ImportError as err:
    logging.warning(_F("Could not import blist: {0}", err))
    logging.warning("Will fallback to surrogate; sortedlist will be slow")
    import PyXWF.Surrogates.blist as blist
