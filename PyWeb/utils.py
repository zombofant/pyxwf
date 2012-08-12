import abc, os
from datetime import datetime

import lxml.etree as ET

class NoInstance(type):
    def _notInstanciable(*args):
        raise TypeError("Cannot instanciate {0}".format(cls.__name__))

    def __new__(mcls, name, bases, dct):
        dct["__new__"] = mcls._notInstanciable
        return super(NoInstance, mcls).__new__(mcls, name, bases, dct)

def splitTag(tag):
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

def addClass(node, cls):
    classes = set(node.get("class", "").split())
    classes.add(cls)
    node.set("class", " ".join(classes))


def fileLastModified(fileref, floatTimes=False):
    """
    If *fileref* is a file name or a file like with associated fileno which
    points to an actual file, return the date of last modification
    stored in the filesystem, **None** otherwise.

    By default, the times are truncated to full seconds. If you need the
    floating point part of the times (if supported by the platform), pass
    ``True`` to *floatTimes*.
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
    if floatTimes:
        mtime = st.st_mtime
    else:
        mtime = int(st.st_mtime)
    return datetime.utcfromtimestamp(mtime)

def unicodeToXPathStr(value):
    return '"'+unicode(value).replace("\"", "\\\"")+'"'

def parseISODate(s):
    if s is None:
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")

def XHTMLToHTML(tree):
    """
    Converts the given ETree *tree* from XHTML to HTML *in-place*. Raises
    :cls:`ValueError` if a non-XHTML namespace is encountered.
    """
    import PyWeb.Namespaces as NS
    xhtmlNS = str(NS.XHTML)
    for item in tree.iter():
        if not isinstance(item.tag, basestring):
            continue
        ns, name = splitTag(item.tag)
        if ns != xhtmlNS:
            raise ValueError("tree contains non-xhtml elements")
        item.tag = name
