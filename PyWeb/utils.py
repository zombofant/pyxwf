import lxml.etree as ET

boolNames = {
    "false": False,
    "no": False,
    "true": True,
    "yes": True
}

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

def getBoolAttr(node, attr, default=None):
    v = node.get(attr)
    if v is None:
        return default
    v = v.lower()
    try:
        return boolNames[v]
    except KeyError:
        raise ValueError("Invalid boolean value: {0}.".format(node.get(attr)))
