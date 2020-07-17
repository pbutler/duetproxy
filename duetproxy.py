#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: ts=4 sts=4 sw=4 tw=88 sta et
"""%prog [options]
Python source code - @todo
"""

__author__ = "Patrick Butler"
__email__ = "pbutler@killertux.org"
__version__ = "0.0.1"

from flask import Flask, request, Response
from urllib.parse import urlparse, urlunparse
import requests
from zeroconf import IPVersion, ServiceInfo, Zeroconf
import socket
from concurrent import futures
import json
from duet import DuetController


app = Flask(__name__)

realnetloc = "192.168.1.6"


@app.route('/config')
def config():
    return "Hello, world"


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
# @app.route('/rr_connect')
def proxy(path):
    global controller
    if request.method == 'GET':
        url = urlparse(request.url)
        if url.path == "/rr_status":
            stype = request.args.get("type")
            data = controller.request_status(stype)
            response = Response(json.dumps(data), 200)
            return response
        else:
            url = url._replace(netloc=realnetloc)
            url = urlunparse(url)
            resp = requests.get(url)
            excluded_headers = ['content-encoding', 'content-length',
                                'transfer-encoding', 'connection']
            headers = [(name, value)
                       for (name, value) in resp.raw.headers.items()
                       if name.lower() not in excluded_headers]
            response = Response(resp.content, resp.status_code, headers)
            return response


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

    parser.add_argument("--token", type=str,
                        help="token for talking with push server")
    parser.add_argument("ip")
    parser.add_argument("password")
    options = parser.parse_args()

    myip = get_ip_address() or get_ip_address2()

    info = ServiceInfo(
        "_http._tcp.local.",
        "DuetProxy._http._tcp.local.",
        addresses=[socket.inet_aton(myip)],
        port=5000,
        properties={"product": "DuetProxy"},
        server="duetproxy.local.",
    )

    controller = DuetController(options.ip,
                                options.password,
                                options.token)
    with futures.ThreadPoolExecutor() as pool:
        pool.submit(controller.poll_loop)
        zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        zeroconf.register_service(info)
        app.run(host="0.0.0.0")
    controller.stop = True

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
