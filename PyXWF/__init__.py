# File name: __init__.py
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
__version__ = "devel"

import logging
import os

pyxwf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_path = os.path.join(pyxwf_path, "data")

if __version__ == "devel":
    import subprocess

    def figure_out_version():
        head = "unknown"
        try:
            head = subprocess.check_output(["git", "rev-parse", "HEAD"])\
                    .decode("utf-8")[:8]
            version = "devel-g" + head
        except OSError:
            logging.warning("Could not figure out devel version, git not installed.")
            return "devel-gunknown"
        except subprocess.CalledProcessError as err:
            logging.warning("Could not figure out devel version, git returned error.")
            return "devel-gerror"

        try:
            status = subprocess.check_output(["git", "status", "--porcelain"])
            dirty = len(status) > 0
        except OSError:
            # we logged that one above already, just ignore it here
            pass
        except subprocess.CalledProcessError:
            logging.warning("Could not figure out dirty state, git-status error'd.")
        else:
            if dirty:
                version += "+dirty"

        return version

    prevcwd = os.getcwd()
    try:

        os.chdir(pyxwf_path)
        __version__ = figure_out_version()
    finally:
        os.chdir(prevcwd)

