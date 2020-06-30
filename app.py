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
from datetime import datetime
import time
import json

app = Flask(__name__)

realnetloc = "192.168.1.6"


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
    return [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
            if not ip.startswith("127.")][0]


class DuetController:
    def __init__(self, targetip, password, token):
        self._targetip = targetip
        self._password = password
        self._token = token
        self._stop = False
        self._cache = {}
        self._temps = {
            "version": 1,
            "time": [],
            "cur": [],
            "active": []
        }
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": "Token {}".format(self._token),
        })
        self._state = None

    def get_rr(self, suffix, params):
        return requests.get(f"http://{self._targetip}/rr_{suffix}", params=params)

    def authenticate(self):
        print("authenticating")
        curtime = datetime.now().isoformat()[0:19]
        resp = self.get_rr("connect", {"password": self._password,
                                       "time": curtime})

        if not (200 <= resp.status_code < 300):
            raise Exception("Authentication failed")
        elif resp.json()["err"] != 0:
            raise Exception("Authentication failed")

    def poll_loop(self):
        print("poll_loop start")
        stype = 1
        last2 = None
        while not self._stop:
            data = self.request_status(stype)
            if data["status"] == "P":
                stype = 3
            else:
                stype = 1

            now = datetime.now()
            if last2 is None or (now - last2).total_seconds() > 10:
                data = self.request_status(2)
                last2 = now
            time.sleep(1)

    def request_status(self, stype):
        now = datetime.now()
        if stype in self._cache:
            last = self._cache[stype][0]
        else:
            last = None
        if last is not None and (now - last).total_seconds() < .25:
            data = self._cache[stype][1]
        else:
            resp = self.get_rr("status", {"type": stype})
            if resp.status_code == 401:
                self.authenticate()
                resp = self.get_rr("status", {"type": stype})
            elif not (200 <= resp.status_code < 300):
                raise Exception("HTTP error {}".format(resp.status_code))

            data = resp.json()
            self._cache[stype] = (now, data)
            # self.handle_temps(data)

            self.update_state(data)

        return data

    def update_state(self, data):
        new_state = data["status"]
        last_state = self._state or "?"
        if new_state != self._state:
            print(self._state)

            self._session.post("https://duetcontroller.killertux.org/api/event/state/",
                               data={"last": last_state, "cur": new_state})
            self._state = new_state

    def handle_temps(self, data):
        now = datetime.now()
        self._temps["time"] += [now]
        self._temps["bed"] += [(
            data["bed"]["current"],
            data["bed"]["active"],
            data["bed"]["standby"],
            data["bed"]["state"],
        )]

        ntools = sum(1 for c in data["current"][1:] if c < 1000)
        if len(self._temps["tools"]) != ntools:
            self._temps["tools"] = [[] for _ in range(ntools)]
        for i, val in enumerate(data["current"][1:]):
            if val > 1000:
                continue
            self._temps["tools"][i] += [(
                val,
                data["tools"]["active"][i][0],
                data["tools"]["standby"][i][0],
                data["state"][i + 1]
            )]


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
