from __future__ import unicode_literals

__all__ = [
    "HTTPStatusBase",

    "HTTPSuccessful",
    "HTTP200", "OK",
    "HTTP201", "Created",
    "HTTP202", "Accepted",
    "HTTP203", "NonAuthorativeInformation",
    "HTTP204", "NoContent",
    "HTTP205", "ResetContent",
    "HTTP206", "PartialContent",

    "HTTPRedirection",
    "HTTP300", "MultipleChoices",
    "HTTP301", "MovedPermanently",
    "HTTP302", "Found",
    "HTTP303", "SeeOther",
    "HTTP304", "NotModified",
    "HTTP305", "UseProxy",
    # "HTTP306", "Unused",
    "HTTP307", "TemporaryRedirect",

    "HTTPClientError",
    "HTTP400", "BadRequest",
    "HTTP401", "Unauthorized",
    "HTTP402", "PaymentRequired",
    "HTTP403", "Forbidden",
    "HTTP404", "NotFound",
    "HTTP405", "MethodNotAllowed",
    "HTTP406", "NotAcceptable",
    "HTTP407", "ProxyAuthenticationRequired",
    "HTTP408", "RequestTimeout",
    "HTTP409", "Conflict",
    "HTTP410", "Gone",
    "HTTP411", "LengthRequired",
    "HTTP412", "PreconditionFailed",
    "HTTP413", "RequestEntityTooLarge",
    "HTTP414", "RequestURITooLong",
    "HTTP415", "RequestedRangeNotSatisfiable",
    "HTTP416", "ExpectationFailed",

    "HTTPServerError",
    "HTTP500", "InternalServerError",
    "HTTP501", "NotImplemented",
    "HTTP502", "BadGateway",
    "HTTP503", "ServiceUnavailable",
    "HTTP504", "GatewayTimeout",
    "HTTP505", "HTTPVersionNotSupported"
]

import abc

try:
    from WebStack.Generic import EndOfResponse
except ImportError:
    EndOfResponse = Exception

class HTTPStatusBase(EndOfResponse):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def code(self):
        pass

    @abc.abstractproperty
    def title(self):
        pass

    def __init__(self, message=None, document=None, template=None, xhtml=None, solutions=[]):
        super(HTTPStatusBase, self).__init__(message)
        self.document = document
        self.template = template
        self.xhtml = xhtml
        self.solutions = list(solutions)

class HTTPSuccessful(HTTPStatusBase):
    pass

class HTTP200(HTTPSuccessful):
    code = 200
    title = "OK"

class HTTP201(HTTPSuccessful):
    code = 201
    title = "Created"

    def __init__(self, location, **kwargs):
        super(HTTP201, self).__init__(**kwargs)
        self.location = location

class HTTP202(HTTPSuccessful):
    code = 202
    title = "Accepted"

class HTTP203(HTTPSuccessful):
    code = 203
    title = "Non-Authorative Information"

class HTTP204(HTTPSuccessful):
    code = 204
    title = "No Content"

class HTTP205(HTTPSuccessful):
    code = 205
    title = "Reset Content"

class HTTP206(HTTPSuccessful):
    code = 206
    title = "Partial Content"

class HTTPRedirection(HTTPStatusBase):
    def __init__(self, location=None, local=True, **kwargs):
        super(HTTPRedirection, self).__init__(**kwargs)
        self.location = location
        self.local = local

class HTTP300(HTTPRedirection):
    code = 300
    title = "Multiple Choices"

class HTTP301(HTTPRedirection):
    code = 301
    title = "Moved Permanently"

class HTTP302(HTTPRedirection):
    code = 302
    title = "Found"

class HTTP303(HTTPRedirection):
    code = 303
    title = "See Other"

class HTTP304(HTTPRedirection):
    code = 304
    title = "Not Modified"

class HTTP305(HTTPRedirection):
    code = 305
    title = "Use Proxy"

class HTTP307(HTTPRedirection):
    code = 307
    title = "Temporary Redirect"


class HTTPClientError(HTTPStatusBase):
    pass

class HTTP400(HTTPClientError):
    code = 400
    title = "Bad Request"

class HTTP401(HTTPClientError):
    code = 401
    title = "Unauthorized"

class HTTP402(HTTPClientError):
    code = 402
    title = "Payment Required"

class HTTP403(HTTPClientError):
    code = 403
    title = "Forbidden"

class HTTP404(HTTPClientError):
    code = 404
    title = "Not Found"

    def __init__(self, resourceName=None, **kwargs):
        kwargs.setdefault("message", resourceName)
        super(HTTP404, self).__init__(**kwargs)
        self.resourceName = resourceName

class HTTP405(HTTPClientError):
    code = 405
    title = "Method Not Allowed"

    def __init__(self, methodName=None, **kwargs):
        super(HTTP405, self).__init__(**kwargs)
        self.methodName = methodName

class HTTP406(HTTPClientError):
    code = 406
    title = "Not Acceptable"

class HTTP407(HTTPClientError):
    code = 407
    title = "Proxy Authentication Required"

class HTTP408(HTTPClientError):
    code = 408
    title = "Request Timeout"

class HTTP409(HTTPClientError):
    code = 409
    title = "Conflict"

class HTTP410(HTTPClientError):
    code = 410
    title = "Gone"

class HTTP411(HTTPClientError):
    code = 411
    title = "Length Required"

class HTTP412(HTTPClientError):
    code = 412
    title = "Precondition Failed"

class HTTP413(HTTPClientError):
    code = 413
    title = "Request Entity Too Large"

class HTTP414(HTTPClientError):
    code = 414
    title = "Request URI Too Long"

class HTTP415(HTTPClientError):
    code = 415
    title = "Unsupported Media Type"

class HTTP416(HTTPClientError):
    code = 416
    title = "Requested Range Not Satisfiable"

class HTTP417(HTTPClientError):
    code = 417
    title = "Expectation Failed"


class HTTPServerError(HTTPStatusBase):
    pass

class HTTP500(HTTPServerError):
    code = 500
    title = "Internal Server Error"

class HTTP501(HTTPServerError):
    code = 501
    title = "Not Implemented"

class HTTP502(HTTPServerError):
    code = 502
    title = "Bad Gateway"

class HTTP503(HTTPServerError):
    code = 503
    title = "Service Unavailable"

class HTTP504(HTTPServerError):
    code = 504
    title = "Gateway Timeout"

class HTTP505(HTTPServerError):
    code = 505
    title = "HTTP Version Not Supported"


OK = HTTP202
Created = HTTP202
Accepted = HTTP202
NonAuthorativeInformation = HTTP203
NoContent = HTTP204
ResetContent = HTTP205
PartialContent = HTTP206
MultipleChoices = HTTP300
MovedPermanently = HTTP301
Found = HTTP302
SeeOther = HTTP303
NotModified = HTTP304
UseProxy = HTTP305
TemporaryRedirect = HTTP307
BadRequest = HTTP400
Unauthorized = HTTP401
PaymentRequired = HTTP402
Forbidden = HTTP403
NotFound = HTTP404
MethodNotAllowed = HTTP405
NotAcceptable = HTTP406
ProxyAuthenticationRequired = HTTP407
RequestTimeout = HTTP408
Conflict = HTTP409
Gone = HTTP410
LengthRequired = HTTP411
PreconditionFailed = HTTP412
RequestEntityTooLarge = HTTP413
RequestURITooLong = HTTP414
UnsupportedMediaType = HTTP415
RequestedRangeNotSatisfiable = HTTP416
ExpectationFailed = HTTP417
InternalServerError = HTTP500
NotImplemented = HTTP501
BadGateway = HTTP502
ServiceUnavailable = HTTP503
GatewayTimeout = HTTP504
HTTPVersionNotSupported = HTTP505
