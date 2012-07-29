import lxml.etree as ET

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
