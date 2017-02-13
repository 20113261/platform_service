#!/usr/bin/env bash

echo 'start insert task'
export PYTHONPATH='/root/data/lib:/root/data/PycharmProjects/data_handling_remote'
/home/hourong/data/venv/py_27/bin/python -u /home/hourong/data/PycharmProjects/data_handling_remote/celery_using/spider_init_total.py
sleep 5
echo 'end insert task'