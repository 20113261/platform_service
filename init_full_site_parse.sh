#!/usr/bin/env bash

echo 'start insert task'
export PYTHONPATH='/root/data/lib:/root/data/PycharmProjects/celery_using'
/home/hourong/data/venv/py_27/bin/python -u /home/hourong/data/PycharmProjects/celery_using/init_full_site_task.py
sleep 5
echo 'end insert task'