#!/usr/bin/python2
from wsgiref.simple_server import make_server
import argparse
import importlib

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        metavar="PATH",
        help="Path to add to the pythonpath."
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
    globals_dict = globals()
    locals_dict = {}
    execfile(args.wsgi_module, globals_dict, locals_dict)

    app = locals_dict[args.application_name]

    httpd = make_server('', args.port, app)
    httpd.serve_forever()



