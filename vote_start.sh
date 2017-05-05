#!/usr/bin/env bash

CURR_PATH=`cd $(dirname $0);pwd;`
cd $CURR_PATH
export PYTHONPATH='/root/data/lib'

/root/data/venv/py_27/bin/python /root/data/PycharmProjects/celery_using/vote_init.py