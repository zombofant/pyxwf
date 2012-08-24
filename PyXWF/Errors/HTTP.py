from __future__ import unicode_literals

__all__ = [
    "HTTPException",

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

from WebStack.Generic import EndOfResponse

class HTTPException(EndOfResponse):
    def __init__(self, statusCode, message=None, statusCodeTitle=None, document=None, template=None, xhtml=None, solutions=[]):
        super(HTTPException, self).__init__(message)
        self.statusCode = statusCode
        self.statusCodeTitle = statusCodeTitle
        self.document = document
        self.template = template
        self.xhtml = xhtml
        self.solutions = list(solutions)

    def fillWithDefaults(self, trans):
        pass

class HTTPSuccessful(HTTPException):
    def __init__(self, statusCode, **kwargs):
        super(HTTPSuccessful, self).__init__(statusCode, message=None, **kwargs)

class HTTP200(HTTPSuccessful):
    def __init__(self, statusCodeTitle="OK", **kwargs):
        super(HTTP200, self).__init__(200, statusCodeTitle=statusCodeTitle, **kwargs)
OK = HTTP200

class HTTP201(HTTPSuccessful):
    def __init__(self, newLocation, statusCodeTitle="Created", **kwargs):
        super(HTTP201, self).__init__(201, statusCodeTitle=statusCodeTitle, **kwargs)
        self.newLocation = newLocation
Created = HTTP201

class HTTP202(HTTPSuccessful):
    def __init__(self, statusCodeTitle="Accepted", **kwargs):
        super(HTTP202, self).__init__(202, statusCodeTitle=statusCodeTitle, **kwargs)
Accepted = HTTP202

class HTTP203(HTTPSuccessful):
    def __init__(self, statusCodeTitle="Non-Authorative Information", **kwargs):
        super(HTTP203, self).__init__(203, statusCodeTitle=statusCodeTitle, **kwargs)
NonAuthorativeInformation = HTTP203

class HTTP204(HTTPSuccessful):
    def __init__(self, statusCodeTitle="No Content", **kwargs):
        super(HTTP204, self).__init__(204, statusCodeTitle=statusCodeTitle, **kwargs)
NoContent = HTTP204

class HTTP205(HTTPSuccessful):
    def __init__(self, statusCodeTitle="Reset Content", **kwargs):
        super(HTTP205, self).__init__(205, statusCodeTitle=statusCodeTitle, **kwargs)
ResetContent = HTTP205

class HTTP206(HTTPSuccessful):
    def __init__(self, statusCodeTitle="Partial Content", **kwargs):
        super(HTTP206, self).__init__(206, statusCodeTitle=statusCodeTitle, **kwargs)
PartialContent = HTTP206


class HTTPRedirection(HTTPException):
    def __init__(self, statusCode, newLocation=None, local=True, **kwargs):
        super(HTTPRedirection, self).__init__(statusCode, **kwargs)
        self.newLocation = newLocation
        self.local = local

class HTTP300(HTTPRedirection):
    def __init__(self, statusCodeTitle="Multiple Choices", **kwargs):
        super(HTTP300, self).__init__(300, statusCodeTitle=statusCodeTitle, **kwargs)
MultipleChoices = HTTP300

class HTTP301(HTTPRedirection):
    def __init__(self, newLocation, statusCodeTitle="Moved Permanently", **kwargs):
        super(HTTP301, self).__init__(301, newLocation=newLocation, statusCodeTitle=statusCodeTitle, **kwargs)
MovedPermanently = HTTP301

class HTTP302(HTTPRedirection):
    def __init__(self, newLocation, statusCodeTitle="Found", **kwargs):
        super(HTTP302, self).__init__(302, newLocation=newLocation, statusCodeTitle=statusCodeTitle, **kwargs)
Found = HTTP302

class HTTP303(HTTPRedirection):
    def __init__(self, newLocation, statusCodeTitle="See Other", **kwargs):
        super(HTTP303, self).__init__(303, newLocation=newLocation, statusCodeTitle=statusCodeTitle, **kwargs)
SeeOther = HTTP303

class HTTP304(HTTPRedirection):
    def __init__(self, statusCodeTitle="Not Modified", **kwargs):
        super(HTTP304, self).__init__(304, statusCodeTitle=statusCodeTitle, **kwargs)
NotModified = HTTP304

class HTTP305(HTTPRedirection):
    def __init__(self, proxyURL, statusCodeTitle="Use Proxy", **kwargs):
        super(HTTP305, self).__init__(305, newLocation=proxyURL, statusCodeTitle=statusCodeTitle, **kwargs)
UseProxy = HTTP305

class HTTP307(HTTPRedirection):
    def __init__(self, newLocation, statusCodeTitle="Temporary Redirect", **kwargs):
        super(HTTP307, self).__init__(307, newLocation=newLocation, statusCodeTitle=statusCodeTitle, **kwargs)
TemporaryRedirect = HTTP307


class HTTPClientError(HTTPException):
    def __init__(self, statusCode, **kwargs):
        super(HTTPClientError, self).__init__(statusCode, **kwargs)

class HTTP400(HTTPClientError):
    def __init__(self, statusCodeTitle="Bad Request", **kwargs):
        super(HTTP400, self).__init__(400, statusCodeTitle=statusCodeTitle, **kwargs)
BadRequest = HTTP400

class HTTP401(HTTPClientError):
    def __init__(self, statusCodeTitle="Unauthorized", **kwargs):
        super(HTTP401, self).__init__(401, statusCodeTitle=statusCodeTitle, **kwargs)
Unauthorized = HTTP401

class HTTP402(HTTPClientError):
    def __init__(self, statusCodeTitle="Payment Required", **kwargs):
        super(HTTP402, self).__init__(402, statusCodeTitle=statusCodeTitle, **kwargs)
PaymentRequired = HTTP402

class HTTP403(HTTPClientError):
    def __init__(self, statusCodeTitle="Forbidden", **kwargs):
        super(HTTP403, self).__init__(403, statusCodeTitle=statusCodeTitle, **kwargs)
Forbidden = HTTP403

class HTTP404(HTTPClientError):
    def __init__(self, resourceName=None, statusCodeTitle="Not Found", **kwargs):
        super(HTTP404, self).__init__(404, message=resourceName, statusCodeTitle=statusCodeTitle, **kwargs)
        self.resourceName = resourceName
NotFound = HTTP404

class HTTP405(HTTPClientError):
    def __init__(self, methodName=None, statusCodeTitle="Method Not Allowed", **kwargs):
        super(HTTP405, self).__init__(405, statusCodeTitle=statusCodeTitle, **kwargs)
        self.methodName = methodName
MethodNotAllowed = HTTP405

class HTTP406(HTTPClientError):
    def __init__(self, statusCodeTitle="Not Acceptable", **kwargs):
        super(HTTP406, self).__init__(406, statusCodeTitle=statusCodeTitle, **kwargs)
NotAcceptable = HTTP406

class HTTP407(HTTPClientError):
    def __init__(self, statusCodeTitle="Proxy Authentication Required", **kwargs):
        super(HTTP407, self).__init__(407, statusCodeTitle=statusCodeTitle, **kwargs)
ProxyAuthenticationRequired = HTTP407

class HTTP408(HTTPClientError):
    def __init__(self, statusCodeTitle="Request Timeout", **kwargs):
        super(HTTP408, self).__init__(408, statusCodeTitle=statusCodeTitle, **kwargs)
RequestTimeout = HTTP408

class HTTP409(HTTPClientError):
    def __init__(self, statusCodeTitle="Conflict", **kwargs):
        super(HTTP409, self).__init__(409, statusCodeTitle=statusCodeTitle, **kwargs)
Conflict = HTTP409

class HTTP410(HTTPClientError):
    def __init__(self, statusCodeTitle="Gone", **kwargs):
        super(HTTP410, self).__init__(410, statusCodeTitle=statusCodeTitle, **kwargs)
Gone = HTTP410

class HTTP411(HTTPClientError):
    def __init__(self, statusCodeTitle="Length Required", **kwargs):
        super(HTTP411, self).__init__(411, statusCodeTitle=statusCodeTitle, **kwargs)
LengthRequired = HTTP411

class HTTP412(HTTPClientError):
    def __init__(self, statusCodeTitle="Precondition Failed", **kwargs):
        super(HTTP412, self).__init__(412, statusCodeTitle=statusCodeTitle, **kwargs)
PreconditionFailed = HTTP412

class HTTP413(HTTPClientError):
    def __init__(self, statusCodeTitle="Request Entity Too Large", **kwargs):
        super(HTTP413, self).__init__(413, statusCodeTitle=statusCodeTitle, **kwargs)
RequestEntityTooLarge = HTTP413

class HTTP414(HTTPClientError):
    def __init__(self, statusCodeTitle="Request URI Too Long", **kwargs):
        super(HTTP414, self).__init__(414, statusCodeTitle=statusCodeTitle, **kwargs)
RequestURITooLong = HTTP414

class HTTP415(HTTPClientError):
    def __init__(self, statusCodeTitle="Unsupported Media Type", **kwargs):
        super(HTTP415, self).__init__(415, statusCodeTitle=statusCodeTitle, **kwargs)
UnsupportedMediaType = HTTP415

class HTTP416(HTTPClientError):
    def __init__(self, statusCodeTitle="Requested Range Not Satisfiable", **kwargs):
        super(HTTP416, self).__init__(416, statusCodeTitle=statusCodeTitle, **kwargs)
RequestedRangeNotSatisfiable = HTTP416

class HTTP417(HTTPClientError):
    def __init__(self, statusCodeTitle="Expectation Failed", **kwargs):
        super(HTTP400, self).__init__(417, statusCodeTitle=statusCodeTitle, **kwargs)
ExpectationFailed = HTTP417


class HTTPServerError(HTTPException):
    def __init__(self, statusCode, **kwargs):
        super(HTTPServerError, self).__init__(statusCode, **kwargs)

class HTTP500(HTTPClientError):
    def __init__(self, statusCodeTitle="Internal Server Error", **kwargs):
        super(HTTP500, self).__init__(500, statusCodeTitle=statusCodeTitle, **kwargs)
InternalServerError = HTTP500

class HTTP501(HTTPClientError):
    def __init__(self, statusCodeTitle="Not Implemented", **kwargs):
        super(HTTP501, self).__init__(501, statusCodeTitle=statusCodeTitle, **kwargs)
NotImplemented = HTTP501

class HTTP502(HTTPClientError):
    def __init__(self, statusCodeTitle="Bad Gateway", **kwargs):
        super(HTTP502, self).__init__(502, statusCodeTitle=statusCodeTitle, **kwargs)
BadGateway = HTTP502

class HTTP503(HTTPClientError):
    def __init__(self, statusCodeTitle="Service Unavailable", **kwargs):
        super(HTTP503, self).__init__(503, statusCodeTitle=statusCodeTitle, **kwargs)
ServiceUnavailable = HTTP503

class HTTP504(HTTPClientError):
    def __init__(self, statusCodeTitle="Gateway Timeout", **kwargs):
        super(HTTP504, self).__init__(504, statusCodeTitle=statusCodeTitle, **kwargs)
GatewayTimeout = HTTP504

class HTTP505(HTTPClientError):
    def __init__(self, statusCodeTitle="HTTP Version Not Supported", **kwargs):
        super(HTTP500, self).__init__(505, statusCodeTitle=statusCodeTitle, **kwargs)
HTTPVersionNotSupported = HTTP505
