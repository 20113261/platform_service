#!/usr/bin/env bash

CURR_PATH=`cd $(dirname $0);pwd;`
cd $CURR_PATH
export PYTHONPATH='/data/lib'
export PATH="$PATH:/usr/local/bin"
export CONFIG_FILE="/data/lib/slave.spider.ini"
export CELERY_LOG_NAME="file_2"
#/usr/local/bin/celery worker -A proj --autoscal=5000,100 -P gevent -l info --logfile=/search/log/celery.log
#/usr/local/bin/celery worker -A proj --autoscal=5000,100 -P gevent -l info
#/usr/local/bin/celery worker -A proj --autoscal=80,5 -c 40 -l info
#/usr/local/bin/celery worker -A proj -c 80 -l info
#
#
# Queue('hotel_suggestion', exchange=Exchange('hotel_suggestion', type='direct'), routing_key='hotel_suggestion'),
#        Queue('full_site_task', exchange=Exchange('full_site_task', type='direct'), routing_key='full_site_task'),
#        Queue('hotel_task', exchange=Exchange('hotel_task', type='direct'), routing_key='hotel_task'),
#        Queue('hotel_list_task', exchange=Exchange('hotel_list_task', type='direct'), routing_key='hotel_list_task'),
/usr/local/bin/celery worker -A proj -P eventlet --autoscale=1000,30 -Q file_downloader -l info -n file_2
#/usr/local/bin/celery worker -A proj --autoscal=10,3 -l info --logfile=/search/log/celery.log