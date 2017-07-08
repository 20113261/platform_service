#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/7 下午4:17
# @Author  : Hou Rong
# @Site    : 
# @File    : full_website_spider_task.py
# @Software: PyCharm
# coding=utf-8
import time
import re
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from .celery import app
from .my_lib.new_hotel_parser.hotel_parser import parse_hotel
from .my_lib.task_module.task_func import update_task
from .my_lib.BaseTask import BaseTask
from .my_lib.PageSaver import save_task_and_page_content
import requests
from my_lib.Common.RedisUrlSaver import UrlSaver

url_saver = UrlSaver()


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='2/s')
def hotel_base_data(self, url, level, **kwargs):
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
        page = requests.get(url, proxies, headers=headers)
        content = page.text
        pass
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)
