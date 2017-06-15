#!/usr/bin/env bash

CURR_PATH=`cd $(dirname $0);pwd;`
cd $CURR_PATH
export PYTHONPATH='/app/lib'
/usr/local/bin/celery worker -A proj --autoscal=40,5 -c 20 -l info