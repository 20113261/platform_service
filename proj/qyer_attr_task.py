# coding=utf-8
import requests
import re
import json
import time
import traceback

from .celery import app
from .my_lib.BaseTask import BaseTask
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent
from .my_lib.task_module.task_func import insert_task, get_task_id


@app.task(bind=True, base=BaseTask, max_retries=7, rate_limit='10/m')
def get_pid_total_page(self, target_url, city_id, part):
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
        html_page = requests.get(target_url, proxies=proxies, headers=headers)
        html_page.encoding = u'utf8'
        content = html_page.text
        pid = re.findall(u'PID :\'(\d+)\'', content)[0]
        total_attr = re.findall(u'景点\((\d+)\)', content)[0]
        # return pid, (int(total_attr) // 15) + 1
        print pid, total_attr
        for page_num in range(1, (int(total_attr) // 15) + 2):
            detail_page.delay(pid, page_num, city_id, part)
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=traceback.format_exc(exc))


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='10/m')
def detail_page(self, pid, page_num, city_id, part):
    x = time.time()
    PROXY = get_proxy(source="Platform")
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    headers = {
        'User-agent': GetUserAgent(),
    }

    try:
        data = {
            u'page': unicode(page_num),
            u'type': u'city',
            u'pid': unicode(pid),
            u'sort': u'32',
            u'subsort': u'all',
            u'isnominate': u'-1',
            u'haslastm': u'false',
            u'rank': u'6'
        }
        json_page = requests.post(u'http://place.qyer.com/poi.php?action=list_json', data=data, proxies=proxies,
                                  headers=headers)
        json_page.encoding = u'utf8'
        content = json_page.text
        j_data = json.loads(content)
        task_data = []
        url_result = []
        for attr in j_data[u'data'][u'list']:
            worker = u'qyer_poi_task'
            args = json.dumps(
                {u'target_url': unicode(u'http:' + attr[u'url']), u'city_id': unicode(city_id)})
            task_id = get_task_id(worker=worker, args=args)
            task_data.append((task_id, worker, args, unicode(part.replace('list', 'detail'))))
            url_result.append(u'http' + attr[u'url'])
        result = insert_task(data=task_data)
        print result
        print url_result
        return result
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=traceback.format_exc(exc))


if __name__ == '__main__':
    # target_url = u'http://place.qyer.com/paris/sight/'
    # pid, total_page = get_pid_total_page(target_url=target_url)
    # print pid, total_page

    # detail_page(20, 2)
    pass
