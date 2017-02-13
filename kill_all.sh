#!/usr/bin/env bash
#ps -aux|grep 'celery' |awk '{print $2}'|xargs kill -9
pkill -9 -f 'celery worker'