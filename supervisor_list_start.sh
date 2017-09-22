#!/usr/bin/env bash

CURR_PATH=`cd $(dirname $0);pwd;`
cd $CURR_PATH
export PYTHONPATH='/data/lib'
export PATH="$PATH:/usr/local/bin"
export CONFIG_FILE="/data/lib/slave.spider.ini"
export CELERY_LOG_NAME="list"
/usr/local/bin/celery worker -A proj -P gevent --autoscale=50,2 -Q hotel_list,poi_list -l info