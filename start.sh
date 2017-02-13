#!/usr/bin/env bash

CURR_PATH=`cd $(dirname $0);pwd;`
cd $CURR_PATH
export PYTHONPATH='/data/lib'
nohup celery worker -A proj --autoscal=2000,500 -P gevent -l info --logfile=/search/log/celery.log &
#nohup celery worker -A proj --autoscal=90,500 -P gevent -l warning --logfile=/search/log/celery.log &
#nohup celery worker -A proj -c 40 -l warning --logfile=/search/log/celery.log &
#celery multi start 2 -A proj --autoscal=900,5000 -P gevent -l warning --logfile=/search/log/celery.log --pidfile=/var/run/celery/%n.pid