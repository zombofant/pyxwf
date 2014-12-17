#!/usr/bin/python2
# File name: serve.py
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
import argparse
import importlib
import sys

from wsgiref.simple_server import make_server

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--add-path",
        metavar="PATH",
        action="append",
        dest="paths",
        default=[],
        help="Add path to PYTHONPATH. May be passed multiple times.",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        metavar="NUMBER",
        help="Port number to listen on, defaults to 8080."
    )
    parser.add_argument(
        "-n", "--application-name",
        default="application",
        metavar="IDENTIFIER",
        help="Python identifier of the wsgi application in MODULE."
    )
    parser.add_argument(
        "wsgi_module",
        metavar="MODULE",
        help="The Python WSGI module to import and run."
    )

    args = parser.parse_args()

    sys.path.extend(args.paths)

    globals_dict = globals()
    locals_dict = {}
    execfile(args.wsgi_module, globals_dict, locals_dict)

    app = locals_dict[args.application_name]

    httpd = make_server('', args.port, app)
    print("Your website is now reachable via:")
    print("  http://localhost:{0}/".format(args.port))
    httpd.serve_forever()



