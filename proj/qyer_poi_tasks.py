# coding=utf-8
import time

import requests
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from .celery import app
from .my_lib.my_qyer_parser.data_obj import DBSession
from .my_lib.my_qyer_parser.my_parser import page_parser
from .my_lib.task_module.task_func import update_task
from .my_lib.BaseTask import BaseTask


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='6/s')
def qyer_poi_task(self, target_url, city_id, **kwargs):
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
        page = requests.get(target_url, proxies=proxies, headers=headers, timeout=240)
        page.encoding = 'utf8'
        content = page.text
        result = page_parser(content=content, target_url=target_url)
        result.city_id = city_id
        if result.name == 'NULL' and result.map_info == 'NULL':
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            session = DBSession()
            session.merge(result)
            session.commit()
            session.close()
            update_task(kwargs['task_id'])
            print "Success with " + PROXY + ' CODE 0'
            update_proxy('Platform', PROXY, x, '0')
        return result
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)
