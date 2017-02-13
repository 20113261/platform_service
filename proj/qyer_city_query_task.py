# coding=utf-8
import json
import re
import time
from urllib import quote

import pymysql
import requests
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from .celery import app
from .my_lib.task_module.task_func import update_task
from .my_lib.BaseTask import BaseTask

clean_pattern = re.compile('<.+?>')


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
    results = j_data['data']['list']

    if isinstance(results, list):
        new_results = results
    elif isinstance(results, dict):
        new_results = results.values()

    for per_result in new_results:
        cn_name = per_result['cn_name']
        en_name = per_result['en_name']
        belong_name = per_result['belong_name']
        url = 'http:' + per_result['url']
        type_name = per_result['type_name']
        if type_name == 'city':
            yield query_string, clean_pattern.sub('', ','.join([cn_name, en_name])), belong_name, url


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def qyer_city_query_task(self, city_name, **kwargs):
    x = time.time()
    PROXY = get_proxy(source="Platform")
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    headers = {
        'User-agent': GetUserAgent(),
        'Referer': "http://www.qyer.com/",
    }

    try:
        conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='SuggestName', charset="utf8")
        with conn as cursor:
            print(city_name)
            quote_string = quote(city_name.encode('utf8'))
            page = requests.get(
                'http://www.qyer.com/qcross/home/ajax?action=search&keyword={0}'.format(
                    quote_string), proxies=proxies, headers=headers)
            page.encoding = 'utf8'
            content = page.text.replace('while(1);', '')
            for line in get_query_data(content=content, query_string=city_name):
                cursor.execute(
                    'insert into QyerSuggestCity (`QueryName`,`Name`,`BelongName`,`Url`) VALUES (%s,%s,%s,%s)',
                    line)
        conn.close()
        update_task(kwargs['task_id'])
        print "Success with " + PROXY + ' CODE 0'
        update_proxy('Platform', PROXY, x, '0')
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)


if __name__ == '__main__':
    pass
