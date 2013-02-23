# File name: test_AcceptHeaders.py
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

        correct_ordering = [p3, p2, p1, p4]
        input_ordering = [p1, p2, p3, p4]
        input_ordering.sort(reverse=True)

        self.assertSequenceEqual(correct_ordering, input_ordering)

    def test_ordering2(self):
        P = AcceptHeaders.Preference
        # from https://tools.ietf.org/html/rfc2616#section-14.1
        # (HTTP/1.1, section 14.1)

        p1 = P("audio/*", 0.2)
        p2 = P("audio/basic", 1.0)

        correct_ordering = [p2, p1]
        input_ordering = [p1, p2]
        input_ordering.sort(reverse=True)

        self.assertSequenceEqual(correct_ordering, input_ordering)


class ListTest(unittest.TestCase):
    def _test_list(self, preflist, expected_qualities):
        for pref, q in expected_qualities:
            calculatedq = preflist.get_quality(pref)
            self.assertEqual(q,
                calculatedq,
                msg="{0} did not get the correct q-value: {1} expected, {2} calculated".format(
                    unicode(pref),
                    q,
                    calculatedq
                )
            )

class AcceptPreferenceList(ListTest):
    def test_parsing(self):
        P = AcceptHeaders.AcceptPreference
        header = """text/plain; q=0.5, text/html,
                    text/x-dvi; q=0.8, text/x-c"""
        l = AcceptHeaders.AcceptPreferenceList()
        l.append_header(header)
        self.assertSequenceEqual(list(l),
            [
                P("text/plain", 0.5),
                P("text/html", 1.0),
                P("text/x-dvi", 0.8),
                P("text/x-c", 1.0),
            ]
        )

    def test_rfc_compliance(self):
        l = AcceptHeaders.AcceptPreferenceList()
        l.append_header("""text/*;q=0.3, text/html;q=0.7, text/html;level=1,
               text/html;level=2;q=0.4, */*;q=0.5""")

        P = AcceptHeaders.AcceptPreference
        expected_qualities = [
            (P.from_header_section("text/html;level=1"),      1.0),
            (P.from_header_section("text/html"),              0.7),
            (P.from_header_section("text/plain"),             0.3),
            (P.from_header_section("image/jpeg"),             0.5),
            (P.from_header_section("text/html;level=2"),      0.4),
            (P.from_header_section("text/html;level=3"),      0.7),
        ]
        self._test_list(l, expected_qualities)

class CharsetPreferenceList(ListTest):
    def test_parsing(self):
        P = AcceptHeaders.CharsetPreference
        header = """iso-8859-5, unicode-1-1;q=0.8"""
        l = AcceptHeaders.CharsetPreferenceList()
        l.append_header(header)
        l.inject_rfc_values()
        self.assertSequenceEqual(list(l),
            [
                P("iso-8859-5", 1.0),
                P("unicode-1-1", 0.8),
                P("iso-8859-1", 1.0)
            ]
        )

    def test_empty(self):
        P = AcceptHeaders.CharsetPreference
        l = AcceptHeaders.CharsetPreferenceList()
        # identical to No Header Present
        l.append_header("")
        l.inject_rfc_values()

        # according to RFC, this is equivalent to all charaters sets are accepted
        self.assertSequenceEqual(list(l),
            [
                P("*", 1.0)
            ]
        )

class LanguagePreferenceList(ListTest):
    def test_parsing(self):
        P = AcceptHeaders.LanguagePreference
        header = """da, en-gb;q=0.8, en;q=0.7"""
        l = AcceptHeaders.LanguagePreferenceList()
        l.append_header(header)
        self.assertSequenceEqual(list(l),
            [
                P("da", 1.0),
                P("en", 0.8, {"sub": "gb"}),
                P("en", 0.7)
            ]
        )

    def test_rfc_compliance(self):
        P = AcceptHeaders.LanguagePreference
        header = """da, en-gb;q=0.8, en;q=0.7"""
        l = AcceptHeaders.LanguagePreferenceList()
        l.append_header(header)

        expected_qualities = [
            (P.from_header_section("da"),                     1.0),
            (P.from_header_section("en-gb"),                  0.8),
            (P.from_header_section("en-us"),                  0.7),
            (P.from_header_section("da-foo"),                 1.0),
            (P.from_header_section("de-de"),                  0.0),
        ]
        self._test_list(l, expected_qualities)
