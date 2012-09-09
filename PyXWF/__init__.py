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

