import traceback

from PyWeb.utils import ET
import PyWeb.Namespaces as NS
import PyWeb.TimeUtils as TimeUtils

import HTTP

class InternalServerError(HTTP.InternalServerError):
    def __init__(self, ctx, exc_type, exc, tb):
        body = self.handleException(ctx, exc_type, exc, tb)
        html = ET.Element(NS.XHTML.html)
        head = ET.SubElement(html, NS.XHTML.head)
        ET.SubElement(head, NS.XHTML.title).text = "Internal Server Error"
        html.append(body)
        super(InternalServerError, self).__init__(xhtml=html)

    def fancyRepr(self, obj, indent=u""):
        newIndent = indent+u"    "
        newIndent2 = indent+u"        "
        if type(obj) == dict:
            items = obj.items()
            if len(items) == 0:
                return u"{}"
            return u"{\n"+newIndent+((u"\n"+newIndent).join(
                u"{0}: {1}".format(self.fancyRepr(key, newIndent2), self.fancyRepr(value, indent+u"        ")) for key, value in obj.items()
            ))+u"\n"+indent+u"}"
        elif type(obj) == list:
            if len(obj) == 0:
                return u"[]"
            return u"[\n"+newIndent+((u"\n"+newIndent).join(self.fancyRepr(item, newIndent2) for item in obj))+u"\n"+indent+u"]"
        elif type(obj) == tuple:
            if len(obj) == 0:
                return u"()"
            return u"(\n"+newIndent+((u"\n"+newIndent).join(self.fancyRepr(item, newIndent2) for item in obj))+u"\n"+indent+u")"
        elif hasattr(obj, "__class__") and obj.__class__ == Cookie:
            return self.fancyRepr(obj.value)
        elif hasattr(obj, "__class__") and obj.__class__ == HeaderDict:
            return self.fancyRepr(obj.headers)
        elif hasattr(obj, "__unicode__") or type(obj) == unicode:
            return u"""[{1}] u"{0}\"""".format(unicode(obj), type(obj))
        elif hasattr(obj, "__str__") or type(obj) == str:
            return u"""[{1}] "{0}\"""".format(str(obj).decode("ascii", "backslashreplace"), type(obj))
        elif obj is None:
            return u"None"
        else:
            return u"[{1}] {0}".format(repr(obj), type(obj))

    def generatePlainTextMessage(self, ctx, exceptionType, exception, tb):
        result = u"".join(traceback.format_exception(exceptionType, exception, tb))
        result += u"""

Query parameters:
GET:
{0}""".format(
            self.fancyRepr(ctx.QueryData) if not False else u"Hidden intentionally",
        )
        return result

    def handleException(self, ctx, exceptionType, exception, tb):
        plainTextMessage = u"""On request: {0} {1}
the following exception occured at {2}:

""".format(ctx.Method, ctx.FullURI, TimeUtils.nowDate().isoformat())
        plainTextMessage += self.generatePlainTextMessage(ctx, exceptionType, exception, tb)
        print(plainTextMessage.encode("utf-8"))

        if False:
            try:
                subject = mailConfig["subject"].format(exceptionType.__name__, unicode(exception))
                to = mailConfig["to"]
                sender = mailConfig["sender"]
                smtp = mailConfig["smtp"]

                mail = MIMEText(plainTextMessage.encode("utf-8"), _charset="utf-8")
                mail["Subject"] = subject
                mail["To"] = ",".join(to)
                mail["From"] = sender
                mail["Date"] = self.model.formatHTTPTimestamp(TimeUtils.now())

                host = smtp["host"]
                port = int(smtp.get("port", 25))
                user = smtp.get("user", None)
                password = smtp.get("password", None)
                secure = smtp.get("secure", None)
                if not secure in ["starttls", "ssl"]:
                    raise ValueError("Invalid value for secure: {0}".format(secure))
                if secure == "ssl":
                    conn = smtplib.SMTP_SSL(host, port)
                else:
                    conn = smtplib.SMTP(host, port)
                    if secure == "starttls":
                        conn.starttls()
                if user is not None and password is not None:
                    conn.login(user, password)
                conn.sendmail(mail["From"], mail["To"], mail.as_string())
                conn.quit()
            except Exception as e :
                print("Could not send exception mail: {0}".format(e))

        body = ET.Element(NS.XHTML.body)
        if True:
            ET.SubElement(body, NS.XHTML.p).text = "Internal Error: {0}".format(unicode(exception))

            section = ET.SubElement(body, NS.XHTML.section, attrib={
                "class": "exc information"
            })
            ET.SubElement(section, NS.XHTML.h3).text = "Error information"

            dl = ET.SubElement(section, NS.XHTML.dl)
            ET.SubElement(dl, NS.XHTML.dt).text = "Exception class:"
            ET.SubElement(dl, NS.XHTML.dd).text = unicode(exceptionType)
            ET.SubElement(dl, NS.XHTML.dt).text = "Message:"
            ET.SubElement(dl, NS.XHTML.dd).text = unicode(exception)


            section = ET.SubElement(body, NS.XHTML.section, attrib={
                "class": "exc information traceback"
            })
            ET.SubElement(section, NS.XHTML.h3).text = "Traceback"
            ET.SubElement(section, NS.XHTML.p).text = "(most recent call last)"
            ul = ET.SubElement(section, NS.XHTML.ul)

            for filename, lineno, funcname, text in traceback.extract_tb(tb):
                li = ET.SubElement(ul, NS.XHTML.li)
                head = ET.SubElement(li, NS.XHTML.div, attrib={
                    "class": "tb-item-head"
                })
                head.text = "File \""
                span = ET.SubElement(head, NS.XHTML.span, attrib={
                    "class": "tb-file"
                })
                span.text = filename
                span.tail = "\", line "
                span = ET.SubElement(head, NS.XHTML.span, attrib={
                    "class": "tb-lineno"
                })
                span.text = unicode(lineno)
                span.tail = ", in "
                span = ET.SubElement(head, NS.XHTML.span, attrib={
                    "class": "tb-func"
                })
                span.text = unicode(funcname)

                if text is not None:
                    code = ET.SubElement(li, NS.XHTML.div, attrib={
                        "class": "tb-item-code"
                    })
                    code.text = unicode(text)

        else:
            p = ET.SubElement(body, NS.XHTML.p)
            p.text = "An internal error has occured. Please report this to "
            a = ET.SubElement(body, NS.XHTML.a, href="mailto:{0}".format(admin["mail"]))
            a.text = admin["name"]
            a.tail = "."
        return body
