#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/22 下午3:04
# @Author  : Hou Rong
# @Site    : 
# @File    : rabbitmq_func.py
# @Software: PyCharm
import re
import json
import requests
import datetime
from requests.auth import HTTPBasicAuth
from proj.config import BROKER_URL

from proj.my_lib.logger import get_logger

logger = get_logger("rabbitmq_func")

host, v_host = re.findall("amqp://.+?@(.+?)/(.+)", BROKER_URL)[0]
TARGET_URL = 'http://{0}:15672/api/queues/{1}'.format(host, v_host)


def detect_msg_num(queue_name):
    target_url = TARGET_URL + '/' + queue_name
    logger.info(target_url)
    page = requests.get(target_url, auth=HTTPBasicAuth('hourong', '1220'))
    content = page.text
    j_data = json.loads(content)

    # 当前 utc 时间
    utc_now_time = datetime.datetime.utcnow()

    # 当前等待时间
    if 'idle_since' in j_data:
        idle_time = datetime.datetime.strptime(j_data["idle_since"], "%Y-%m-%d %H:%M:%S")
    else:
        idle_time = utc_now_time

    idle_seconds = (utc_now_time - idle_time).seconds

    count = j_data.get('messages_ready')
    max_count = j_data.get('messages_unacknowledged')
    message_count = int(count)
    max_message_count = int(max_count)
    return idle_seconds, message_count, max_message_count


if __name__ == '__main__':
    print(detect_msg_num("celery"))
