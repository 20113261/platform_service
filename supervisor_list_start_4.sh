#!/usr/bin/env bash

CURR_PATH=`cd $(dirname $0);pwd;`
cd $CURR_PATH
export PYTHONPATH='/data/lib'
export PATH="$PATH:/usr/local/bin"
export CONFIG_FILE="/data/lib/slave.spider.ini"
export CELERY_LOG_NAME="list_4"
export CELERY_WORKER_NAME=$CELERY_LOG_NAME"_"`hostname`
echo $CELERY_WORKER_NAME

/usr/local/bin/celery worker -A proj -P gevent --autoscale=1500,3 -Q hotel_list,poi_list -l info -n $CELERY_WORKER_NAME