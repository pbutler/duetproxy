#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: ts=4 sts=4 sw=4 tw=88 sta et
"""%prog [options]
Python source code - @todo
"""

__author__ = "Patrick Butler"
__email__ = "pbutler@killertux.org"
__version__ = "0.0.1"

import json
from pathlib import Path
import logging
import requests

logger = logging.getLogger(__name__)


class Conf(object):
    """A class to handle reading and writing of config file settings"""

    def __init__(self):
        """Initialize with set path(s)"""
        self._base_dir = Path.home()
        self._path = self._base_dir / ".duetconf"
        self._path_tmp: Path = self._base_dir / ".duetconf.tmp"
        self._last_mtime = None
        self._last_read = None
        self._conf = {}
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": "Token {}".format(self._token),
        })

    def load(self):
        """Update internal config by reading file on disk if and only if the file on
        disk is newer
        :returns: whether config was updated
        """
        if self._path.exists():
            cur_mtime = self._path.stat().st_mtime
            logging.debug("Checking mtime")
            if self._last_mtime is None or cur_mtime > self._last_mtime:
                with open(self._path) as fp:
                    self._last_mtime = cur_mtime
                    try:
                        logging.debug("Loading config")
                        self._conf = json.load(fp)
                        return True
                    except Exception as e:
                        logging.error(e)
                        self._conf = {}
            else:
                logging.debug("conf update not detected")
        else:
            logging.debug("Conf file does not exist")
            self._conf = {}
        return False

    def __getitem__(self, key):
        """Read and return config, but only read once a second

        :param key: key to lookup
        :returns: value of config with key or None if no value is available

        """
        # now = time.time()
        # if self._last_read is None or (now - self._last_read) > 1:
        #     self._last_read = now
        #     self.read()

        if key in self._conf:
            return self._conf[key]
        else:
            return None

    def __setitem__(self, key, value):
        """Set a config key with value

        :param key: TODO
        :param value: TODO
        :returns: TODO

        """
        self._conf[key] = value

    def save(self):
        """Save config to file atomically

        :returns: TODO

        """
        logging.debug("Saving config")
        with open(self._path_tmp, "w") as fp:
            json.dump(self._conf, fp, indent=4)
        self._path_tmp.rename(self._path)


def main():
    """Run tests for conf library"""
    logging.basicConfig(level=logging.DEBUG)
    conf1 = Conf()
    conf1["test"] = 1
    conf1.save()

    conf2 = Conf()
    conf2.load()
    logging.debug("test=%d", conf2["test"])
    conf2.load()

    conf1["test"] = 2
    conf1.save()

    conf2.load()
    logging.debug("test=%d", conf2["test"])


if __name__ == "__main__":
    main()
