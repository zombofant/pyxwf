from WebStack.Generic import ContentType


xhtml = "application/xhtml+xml"
html = "text/html"
plainText = "text/plain"

normalization = {
    "application/xhtml+xml": xhtml,
    "text/xhtml": xhtml,
    "application/xhtml": xhtml,
    "text/html": html,
}

def normalizedName(contentType):
    if not isinstance(ContentType, contentType):
        contentTypeName = str(contentType)
        charset = None
    else:
        contentTypeName = contentType.media_type
        charset = contentType.charset
    try:
        return normalization[contentTypeName]
    except KeyError:
        return contentTypeName
