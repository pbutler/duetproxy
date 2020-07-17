#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: ts=4 sts=4 sw=4 tw=88 sta et
"""%prog [options]
Python source code - @todo
"""

__author__ = "Patrick Butler"
__email__ = "pbutler@killertux.org"
__version__ = "0.0.1"

import time
import socket
from zeroconf import IPVersion, ServiceInfo, Zeroconf


def get_ip_address2():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def get_ip_address():
    ips = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
           if not ip.startswith("127.")]
    if ips:
        return ips[0]
    else:
        return None


def main(args):
    global controller
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose",
                        help="don't print status messages to stdout")
    parser.add_argument("--version", action="version",
                        version="%(prog)s " + __version__)
    options = parser.parse_args()

    myip = get_ip_address() or get_ip_address2()

    info = ServiceInfo(
        "_https._tcp.local.",
        "DuetProxy._https._tcp.local.",
        addresses=[socket.inet_aton(myip)],
        port=443,
        properties={"product": "DuetProxy"},
        server="duetproxy.local.",
    )

    zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
    zeroconf.register_service(info)
    while True:
        time.sleep(1.)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
