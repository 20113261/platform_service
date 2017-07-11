#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/4 下午6:47
# @Author  : Hou Rong
# @Site    : 
# @File    : suggestion_task.py
# @Software: PyCharm

# coding=utf-8
import sys

reload(sys)

sys.setdefaultencoding('utf8')

import requests
import re
import json
import time
import datetime
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from .celery import app
from .my_lib.BaseTask import BaseTask
from .my_lib.task_module.task_func import update_task
from .my_lib.PageSaver import save_suggestions


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='6/s')
def ctrip_suggestion_task(self, city_id, key_word, annotation=-1, **kwargs):
    x = time.time()
    PROXY = get_proxy(source="Platform")
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    headers = {
        'User-agent': GetUserAgent()
    }
    try:
        req_url = 'http://hotels.ctrip.com/international/Tool/cityFilter.ashx?keyword={0}'.format(key_word)
        page = requests.get(req_url, headers=headers, proxies=proxies)
        data_str = re.findall('cQuery.jsonpResponse=([\s\S]+?);', page.text)[0]
        j_data = json.loads(data_str)
        if j_data['key'] != "" and j_data['data'] == "":
            if kwargs.get('task_id'):
                update_task(kwargs['task_id'])

            return "Empty Suggestion"
        if j_data['data']:
            if kwargs.get('task_id'):
                save_suggestions({
                    'source': 'ctrip',
                    'city_id': city_id,
                    'key_word': key_word,
                    'u_time': datetime.datetime.now(),
                    'annotation': annotation,
                    'data': j_data
                }, 'ctrip')
                update_task(kwargs['task_id'])
            print "Success with " + PROXY + ' CODE 0'
            update_proxy('Platform', PROXY, x, '0')
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)
