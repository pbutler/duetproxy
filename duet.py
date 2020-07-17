#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: ts=4 sts=4 sw=4 tw=88 sta et
"""Python interface to the DuetController"""

import datetime

import requests


class DuetController:
    """Python interface to the DuetController"""

    def __init__(self, targetip, password):
        """Use the targetip and password to login ot the DC"""
        self._targetip = targetip
        self._password = password
        self._stop = False
        self._cache = {}
        self._temps = {
            "version": 1,
            "time": [],
            "cur": [],
            "active": []
        }
        self._state = None

    def get_rr(self, suffix, params):
        """Create a request on the duet 2.0 controller"""
        return requests.get(f"http://{self._targetip}/rr_{suffix}", params=params)

    def authenticate(self):
        """Authenticate with the controller"""
        print("authenticating")
        curtime = datetime.now().isoformat()[0:19]
        resp = self.get_rr("connect", {"password": self._password,
                                       "time": curtime})

        if not (200 <= resp.status_code < 300):
            raise Exception("Authentication failed")
        elif resp.json()["err"] != 0:
            raise Exception("Authentication failed")

    def poll(self, stype=1):
        """Poll for a status update and returns said data from update

        :param stype: integer of 1, 2, or 3 that defines the status type as defined
        here https://reprap.org/wiki/RepRap_Firmware_Status_responses
        :returns: tuple (dict containing data, stype) where stype is the suggested type
        of the next request

        """
        data = self.request_status(stype)
        if data["status"] == "P":
            stype = 3
        else:
            stype = 1
        return data, stype

    def request_status(self, stype):
        """Download requests status and authenticate if need be

        :param stype: status type
        :returns: data or raise an exception

        """
        resp = self.get_rr("status", {"type": stype})
        if resp.status_code == 401:
            self.authenticate()
            resp = self.get_rr("status", {"type": stype})

        if not (200 <= resp.status_code < 300):
            raise Exception("HTTP error {}".format(resp.status_code))
        else:
            data = resp.json()
            return data

    def handle_temps(self, data):
        """Gather and store temperatures over time"""
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
