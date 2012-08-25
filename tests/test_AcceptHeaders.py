import unittest

import PyXWF.AcceptHeaders as AcceptHeaders

class Preference(unittest.TestCase):
    def test_ordering(self):
        P = AcceptHeaders.Preference
        # from https://tools.ietf.org/html/rfc2616#section-14.1
        # (HTTP/1.1, section 14.1)

        p1 = P("text/*", 1.0)
        p2 = P("text/html", 1.0)
        p3 = P("text/html", 1.0, parameters={"level": "1"})
        p4 = P("*/*", 1.0)

        correctOrdering = [p3, p2, p1, p4]
        inputOrdering = [p1, p2, p3, p4]
        inputOrdering.sort(reverse=True)

        self.assertSequenceEqual(correctOrdering, inputOrdering)

    def test_ordering2(self):
        P = AcceptHeaders.Preference
        # from https://tools.ietf.org/html/rfc2616#section-14.1
        # (HTTP/1.1, section 14.1)

        p1 = P("audio/*", 0.2)
        p2 = P("audio/basic", 1.0)

        correctOrdering = [p2, p1]
        inputOrdering = [p1, p2]
        inputOrdering.sort(reverse=True)

        self.assertSequenceEqual(correctOrdering, inputOrdering)


class AcceptPreferenceList(unittest.TestCase):
    def test_parsing(self):
        P = AcceptHeaders.AcceptPreference
        header = """text/plain; q=0.5, text/html,
                    text/x-dvi; q=0.8, text/x-c"""
        l = AcceptHeaders.AcceptPreferenceList()
        l.appendHeader(header)
        self.assertSequenceEqual(list(l),
            [
                P("text/plain", 0.5),
                P("text/html", 1.0),
                P("text/x-dvi", 0.8),
                P("text/x-c", 1.0),
            ]
        )

    def test_rfcCompliance(self):
        l = AcceptHeaders.AcceptPreferenceList()
        l.appendHeader("""text/*;q=0.3, text/html;q=0.7, text/html;level=1,
               text/html;level=2;q=0.4, */*;q=0.5""")

        P = AcceptHeaders.AcceptPreference
        expectedPrecedence = [
            (P.fromHeaderSection("text/html;level=1"),     1.0),
            (P.fromHeaderSection("text/html"),             0.7),
            (P.fromHeaderSection("text/plain"),            0.3),
            (P.fromHeaderSection("image/jpeg"),            0.5),
            (P.fromHeaderSection("text/html;level=2"),     0.4),
            (P.fromHeaderSection("text/html;level=3"),     0.7),
        ]

        for pref, q in expectedPrecedence:
            candidates = l.getCandidates([pref])
            precedence = candidates.pop()[0]
            self.assertEqual(q, precedence, msg="{0} did not get the correct q-value: {1} expected, {2} calculated".format(
                pref,
                q,
                precedence
            ))

class CharsetPreferenceList(unittest.TestCase):
    def test_parsing(self):
        P = AcceptHeaders.CharsetPreference
        header = """iso-8859-5, unicode-1-1;q=0.8"""
        l = AcceptHeaders.CharsetPreferenceList()
        l.appendHeader(header)
        l.injectRFCValues()
        self.assertSequenceEqual(list(l),
            [
                P("iso-8859-5", 1.0),
                P("unicode-1-1", 0.8),
                P("iso-8859-1", 1.0)
            ]
        )

class LanguagePreferenceList(unittest.TestCase):
    def test_parsing(self):
        P = AcceptHeaders.LanguagePreference
        header = """da, en-gb;q=0.8, en;q=0.7"""
        l = AcceptHeaders.LanguagePreferenceList()
        l.appendHeader(header)
        self.assertSequenceEqual(list(l),
            [
                P("da", 1.0),
                P("en", 0.8, {"sub": "gb"}),
                P("en", 0.7)
            ]
        )

    def test_rfcCompliance(self):
        P = AcceptHeaders.LanguagePreference
        header = """da, en-gb;q=0.8, en;q=0.7"""
        l = AcceptHeaders.LanguagePreferenceList()
        l.appendHeader(header)

        expectedPrecedence = [
            (P.fromHeaderSection("da"),                    1.0),
            (P.fromHeaderSection("en-gb"),             0.8),
            (P.fromHeaderSection("en-us"),            0.7),
            (P.fromHeaderSection("da-foo"),            1.0),
            (P.fromHeaderSection("de-de"),     0.0),
        ]

        for pref, q in expectedPrecedence:
            candidates = l.getCandidates([pref])
            try:
                precedence = candidates.pop()[0]
            except IndexError:
                precedence = 0
            self.assertEqual(q, precedence, msg="{0} did not get the correct q-value: {1} expected, {2} calculated".format(
                unicode(pref),
                q,
                precedence
            ))
