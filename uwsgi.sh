#!/bin/bash

eUID=$(id -u nobody)
eGID=$(id -g nobody)

. /home/pi/.virtualenvs/duetproxy/bin/activate
uwsgi \
    --chdir=/home/pi/duetproxy \
    --module=duetproxy:app \
    --master --pidfile=/var/run/duetproxy.pid \
    --socket=/var/run/duetproxy.sock --chmod-socket=666 --chown-socket=nobody \
    --processes=5 \
    --uid=$eUID --gid=$eGID \
    --harakiri=20 \
    --max-requests=5000 \
    --vacuum \
    --home=/home/pi/.virtualenvs/duetproxy  \
    --touch-reload /home/pi/duetproxy/uwsgi.sh \
    --daemonize=/var/log/duet.log   # background the process
