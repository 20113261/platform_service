import requests
import re
import pyquery
import pymysql
import time

from util.UserAgent import GetUserAgent
from .celery import app
from common.common import get_proxy, update_proxy
from .my_lib.BaseTask import BaseTask


def insert_db(data):
    conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', charset='utf8', db='tripadvisor')
    with conn as cursor:
        result = cursor.executemany('insert into city(url, img, rank, name, country_id) VALUES (%s,%s,%s,%s,%s)', data)
    conn.close()
    return result


def _parse_city(content, target_url):
    doc = pyquery.PyQuery(content)
    doc.make_links_absolute(target_url)
    for city in doc('.popularCity').items():
        city_url = city.attr.href
        img_url = city('.sizedThumb>img').attr.src
        rank_num = re.findall('(\d+)', city('.rankNum').text().replace(',', ''))[0]
        city_name = city('.name').text()
        yield city_url, img_url, rank_num, city_name


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='15/s')
def get_cities(self, gid, country_id, offset):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    headers = {
        'User-agent': GetUserAgent()
    }
    try:
        target_url = 'http://www.tripadvisor.cn/TourismChildrenAjax?geo={0}&offset={1}&desktop=true'.format(gid, offset)
        page = requests.get(target_url, headers=headers, proxies=proxies)
        page.encoding = 'utf8'
        content = page.text

        res = re.findall('ta.store\(\'tourism.popularCitiesMaxPage\', \'(\d+)\'\);', content)

        has_next = False
        if res is not None and res != []:
            if offset < int(res[0]):
                has_next = True

        result = []
        for line in _parse_city(content=content, target_url=target_url):
            per_city = list(line)
            per_city.append(country_id)
            result.append(per_city)

        print insert_db(result)

        if has_next:
            get_cities.delay(gid, country_id, offset + 1)
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)


def get_task():
    conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', charset='utf8', db='tripadvisor')
    with conn as cursor:
        cursor.execute('select url, id from country')
        for url, country_id in cursor.fetchall():
            yield re.findall('-g(\d+)', url)[0], country_id, 0
    conn.close()


if __name__ == '__main__':
    # get_cities('293939', 134, 0)
    for line in get_task():
        print line
