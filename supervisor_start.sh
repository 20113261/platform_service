#!/usr/bin/env bash

CURR_PATH=`cd $(dirname $0);pwd;`
cd $CURR_PATH
export PYTHONPATH='/data/lib'
#/usr/local/bin/celery worker -A proj --autoscal=5000,100 -P gevent -l info --logfile=/search/log/celery.log
/usr/local/bin/celery worker -A proj --autoscal=5000,100 -P gevent -l info
#/usr/local/bin/celery worker -A proj --autoscal=10,3 -l info --logfile=/search/log/celery.log