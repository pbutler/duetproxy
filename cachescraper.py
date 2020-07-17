#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: ts=4 sts=4 sw=4 tw=88 sta et
"""%prog [options]
Python source code - @todo
"""

__author__ = "Patrick Butler"
__email__ = "pbutler@killertux.org"
__version__ = "0.0.1"

from conf import Conf
from duet import DuetController
from redis import Redis


class Scraper:
    def update_state(self, data):
        """TODO: Docstring for update_state.

        :param arg1: TODO
        :returns: TODO

        """
        new_state = data["status"]
        last_state = self._state or "?"
        if new_state != self._state:
            print(self._state)

            self._session.post("https://duetcontroller.killertux.org/api/event/state/",
                               data={"last": last_state, "cur": new_state})
            self._state = new_state

def run_loop():
    """Run cache loop
    :returns: TODO
    """
    conf = Conf()
    updated = conf.read()


def main(args):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose",
                        help="don't print status messages to stdout")
    parser.add_argument("--version", action="version",
                        version="%(prog)s " + __version__)
    # parser.add_argument("args", metavar="args", type=str, nargs="*",
    #                     help="an integer for the accumulator")
    options = parser.parse_args()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))

