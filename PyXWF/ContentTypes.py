# encoding=utf-8
# File name: ContentTypes.py
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
"""
Contains only a few content type declarations. These may be used around the
application and it's better to have them in one place.

It also provides normalization functionality for content types which are often
used interchangably. Returns the “right” content type.
"""

xhtml = "application/xhtml+xml"
html = "text/html"
plaintext = "text/plain"
Atom = "application/atom+xml"
PyWebXML = "application/x-pywebxml"
Markdown = "text/x-markdown"

normalization = {
    "application/xhtml+xml": xhtml,
    "text/xhtml": xhtml,
    "application/xhtml": xhtml,
    "text/html": html,
}
