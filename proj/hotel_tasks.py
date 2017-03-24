# coding=utf-8
import time

import requests
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from .celery import app
from .my_lib.new_hotel_parser.hotel_parser import parse_hotel
from .my_lib.task_module.task_func import update_task
from .my_lib.BaseTask import BaseTask
from .my_lib.FileSaver import save_file


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='20/s')
def hotel_base_data(self, source, url, other_info, part, **kwargs):
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
        page = requests.get(url, proxies=proxies, headers=headers, timeout=240)
        page.encoding = 'utf8'
        content = page.text
        # agoda 特殊情况 start

        if source == 'agoda':
            url_about = 'https://www.agoda.com/NewSite/zh-cn/Hotel/AboutHotel?hotelId={0}&languageId=8&hasBcomChildPolicy=False'.format(
                other_info['source_id'])
            page_about = requests.get(url=url_about, headers=headers)
            page_about.encoding = 'utf8'
            about_content = page_about.text
            other_info['about_content'] = about_content

        # agoda end

        # venere start
        if source == 'venere':
            update_task(kwargs['task_id'])

        # venere end

        # booking start

        headers['Referer'] = 'http://www.booking.com'

        # booking end
        save_file(kwargs['task_id'], self.request.id, content)
        result = parse_hotel(content=content, url=url, other_info=other_info, source=source, part=part)

        if not result:
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            update_task(kwargs['task_id'])
            print "Success with " + PROXY + ' CODE 0'
            update_proxy('Platform', PROXY, x, '0')
        return result
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)
