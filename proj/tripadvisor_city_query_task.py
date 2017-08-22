# coding=utf-8
import json
import time
from urllib import quote
import traceback

import pymysql
import requests
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from proj.celery import app
from proj.my_lib.task_module.task_func import update_task
from proj.my_lib.BaseTask import BaseTask


def get_city_name():
    _name_set = set()
    conn = pymysql.connect(host='10.10.154.38', user='reader', passwd='miaoji1109', db='devdb', charset="utf8")
    with conn as cursor:
        cursor.execute('select distinct name from city')
        for line in cursor.fetchall():
            _name_set.add(line[0])
    return _name_set


def get_query_data(content, query_string):
    j_data = json.loads(content)

    for result in j_data['results']:
        name = result['name'].replace('<b>', '').replace('</b>', '')
        coords = ','.join(result.get('coords', '').split(',')[::-1])
        url = 'http://www.tripadvisor.cn' + result['url']
        if 'Tourism-g' in url:
            if result['type'] == 'GEO':
                yield query_string, name, coords, url


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def tripadvisor_city_query_task(self, city_name, **kwargs):
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
        conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='SuggestName', charset="utf8")
        with conn as cursor:
            print(city_name)
            quote_string = quote(city_name.encode('utf8'))
            page = requests.get(
                'http://www.tripadvisor.cn/TypeAheadJson?interleaved=true&types=geo%2Ctheme_park%2Cair&neighborhood_geos=true&link_type=geo&details=true&max=6&hglt=true&query={0}&action=API&uiOrigin=GEOSCOPE&source=GEOSCOPE'.format(
                    quote_string), proxies=proxies, headers=headers)
            page.encoding = 'utf8'
            content = page.text.replace('while(1);', '')
            for line in get_query_data(content=content, query_string=city_name):
                cursor.execute(
                    'insert into TripAdvisorSuggestCity (`QueryName`,`Name`,`coords`,`Url`) VALUES (%s,%s,%s,%s)',
                    line)
        conn.close()
        update_task(kwargs['task_id'])
        print "Success with " + PROXY + ' CODE 0'
        update_proxy('Platform', PROXY, x, '0')
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=traceback.format_exc(exc))


if __name__ == '__main__':
    pass
