#!/usr/bin/env bash

CURR_PATH=`cd $(dirname $0);pwd;`
cd $CURR_PATH
export PYTHONPATH='/app/lib'
/usr/local/bin/celery worker -A proj -P eventlet -Q full_site_task --autoscale=2000,200 -l info