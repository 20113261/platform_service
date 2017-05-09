# coding=utf8
from __future__ import absolute_import

import json
import random
import time
import traceback
import pymysql
from cStringIO import StringIO

import MySQLdb
import db_localhost
import os
import re
import requests
from celery import platforms
from common.common import get_proxy, update_proxy, save_image
from lxml import html
from pyquery import PyQuery
from util.UserAgent import GetUserAgent

from .celery import app
from .my_lib.attr_parser import insert_db as attr_insert_db
from .my_lib.attr_parser import parse as attr_parser
from .my_lib.hotel_comment.booking import parser as booking_comment_parser
from .my_lib.hotel_comment.expedia import parser as expedia_comment_parser
from .my_lib.hotel_comment.venere import parser as venere_comment_parser
from .my_lib.is_complete_scale_ok import is_complete_scale_ok
from .my_lib.rest_parser import parse as rest_parser
from .my_lib.shop_parser import parse as shop_parser
from .my_lib.tp_comment_parser import parse, long_comment_parse, insert_db
from .my_lib.BaseTask import BaseTask
from .my_lib.task_module.task_func import get_task_id, update_task, insert_task
from .my_lib.get_rate_limit import get_rate_limit

platforms.C_FORCE_ROOT = True

_rate_limit_dict = get_rate_limit()


@app.task
def add_task():
    for i in range(10):
        add.delay(random.randint(1, 10), random.randint(1, 10))


@app.task
def add_image_url():
    url_list_file = ['img_url_1101', 'img_url_1103', 'img_url_test']
    count = 0
    for file_name in url_list_file:
        path = '/search/image/' + file_name + '_celery'
        if os.path.exists(path):
            already_downloaded = set(os.listdir(path))
        else:
            already_downloaded = set([])
        for url in open('/tmp/' + file_name):
            if hashlib.md5(url.strip()).hexdigest() + '.jpg' not in already_downloaded:
                # get_images.delay(file_name + '_celery', url.strip())
                count += 1
    return count


@app.task
def add(x, y):
    print x, y, x + y
    return x + y


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def get_comment(self, target_url, language, miaoji_id, special_str, **kwargs):
    if language == 'en':
        data = {
            'mode': 'filterReviews',
            'filterLang': 'en'
        }
    elif language == 'zhCN':
        data = {
            'mode': 'filterReviews',
            'filterLang': 'zh_CN'
        }
    else:
        return "Error, no such language"

    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    headers = {
        'User-agent': GetUserAgent()
    }

    if data != '':
        try:
            page = requests.post(target_url, data, headers=headers, proxies=proxies, timeout=120)
            page.encoding = 'utf8'
            res = parse(page.text, target_url, language, miaoji_id, special_str)
            if res == 0:
                update_proxy('Platform', PROXY, x, '23')
                self.retry(countdown=120)
            else:
                update_task(kwargs['task_id'])
                update_proxy('Platform', PROXY, x, '0')
                print "Success with " + PROXY + ' CODE 0'
        except Exception as exc:
            update_proxy('Platform', PROXY, x, '23')
            self.retry(exc=exc, countdown=120)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='20/s')
def get_long_comment(self, target_url, language, miaoji_id, special_str):
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
        page = requests.get(target_url, headers=headers, proxies=proxies, timeout=120)
        page.encoding = 'utf8'
        data = long_comment_parse(page.content, target_url, language, miaoji_id)
        update_proxy('Platform', PROXY, x, '0')
        print "Success with " + PROXY + ' CODE 0'
        return insert_db((data,), 'tp_comment_' + special_str)
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='45/s')
def get_lost_attr(self, target_url, city_id, **kwargs):
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
        page = requests.get(target_url, proxies=proxies, headers=headers, timeout=15)
        page.encoding = 'utf8'
        result = attr_parser(page.content, target_url)
        if result == 'Error':
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            print "Success with " + PROXY + ' CODE 0'
            try:
                print attr_insert_db(result, city_id)
                update_task(task_id=kwargs['task_id'])
                update_proxy('Platform', PROXY, x, '0')
            except Exception as exc:
                self.retry(exc=exc)

        return result
        # data = long_comment_parse(page.content, target_url, language)
        # return insert_db([data, ])
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)


def _get_site_url(target_url):
    PROXY = get_proxy(source="Platform")
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(target_url, proxies=proxies, headers=headers, allow_redirects=False)
    source_site_url = page.headers['location']
    print source_site_url
    # source_site_url = page.url
    if source_site_url != '' and source_site_url is not None:
        return source_site_url.replace('#_=_', '')
    else:
        return "Error"


def update_site_url(site_url, source_id, table_name):
    sql = 'update {0} set site=%s where id=%s'.format(table_name)
    return db_localhost.ExecuteSQL(sql, (site_url, source_id))


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='60/s')
def get_site_url(self, target_url, source_id, table_name):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    try:
        res = _get_site_url(target_url)
        if res == 'Error':
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            print "Success with " + PROXY + ' CODE 0'
            update_proxy('Platform', PROXY, x, '0')
            update_site_url(res, source_id, table_name=table_name)
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='45/s')
def get_lost_rest(self, target_url, **kwargs):
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
        page = requests.get(target_url, proxies=proxies, headers=headers, timeout=15)
        page.encoding = 'utf8'
        result = rest_parser(page.content, target_url, city_id=city_id)
        if result == 'Error':
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            print "Success with " + PROXY + ' CODE 0'
            update_proxy('Platform', PROXY, x, '0')

        # print attr_insert_db(result)
        update_task(task_id=kwargs['task_id'])
        return result
        # data = long_comment_parse(page.content, target_url, language)
        # return insert_db([data, ])
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='45/s')
def get_lost_shop(self, target_url, city_id, **kwargs):
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
        page = requests.get(target_url, proxies=proxies, headers=headers, timeout=15)
        page.encoding = 'utf8'
        result = shop_parser(page.content, target_url, city_id)
        if result == 'Error':
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            print "Success with " + PROXY + ' CODE 0'
            update_task(task_id=kwargs['task_id'])
            update_proxy('Platform', PROXY, x, '0')
        return result
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc, countdown=2)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='45/s')
def get_lost_rest_new(self, target_url, city_id, **kwargs):
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
        page = requests.get(target_url, headers=headers, proxies=proxies, timeout=15)
        page.encoding = 'utf8'
        result = rest_parser(page.content, target_url, city_id)
        if result == 'Error':
            self.retry()
        else:
            update_task(task_id=kwargs['task_id'])
            update_proxy('Platform', PROXY, x, '23')
        return result
    except Exception as exc:
        self.retry(exc=exc)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def get_lost_rest_no_proxy(self, target_url):
    try:
        page = requests.get(target_url, timeout=15)
        page.encoding = 'utf8'
        result = rest_parser(page.content, target_url)
        if result == 'Error':
            self.retry()
        return result
    except Exception as exc:
        self.retry(exc=exc)


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='10/s')
def get_images(self, source, target_url, **kwargs):
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
        page = requests.get(target_url, headers=headers, proxies=proxies, timeout=120)
        f = StringIO(page.content)
        flag, h, w = is_complete_scale_ok(f)
        file_name = hashlib.md5(target_url).hexdigest()
        if flag in [1, 2]:
            update_proxy('Platform', PROXY, x, '22')
            print "Image Error with Proxy " + PROXY + " used time " + str(time.time() - x)
            self.retry(countdown=2)
        else:
            print "Success with " + PROXY + ' CODE 0 used time ' + str(time.time() - x)
            if 'task_id' in kwargs.keys():
                update_task(kwargs['task_id'])
            save_image(source, file_name, page.content)
            update_proxy('Platform', PROXY, x, '0')
        return flag, h, w, file_name
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '22')
        print "Image Error with Proxy " + PROXY + ' used time ' + str(time.time() - x)
        self.retry(exc=exc, countdown=2)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='60/s')
def booking_comment(self, target_url, **kwargs):
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
        page = requests.get(target_url, proxies=proxies, headers=headers, timeout=120)
        page.encoding = 'utf8'
        result = booking_comment_parser(page.text, target_url)
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


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='60/s')
def venere_comment(self, target_url, **kwargs):
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
        page = requests.get(target_url, proxies=proxies, headers=headers, timeout=120)
        page.encoding = 'utf8'
        result = venere_comment_parser(page.text, target_url)
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


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='120/s')
def expedia_comment(self, target_url, **kwargs):
    headers = {
        'User-agent': GetUserAgent()
    }
    try:
        page = requests.get(target_url, headers=headers, timeout=180)
        page.encoding = 'utf8'
        result = expedia_comment_parser(page.text, target_url)
        if not result:
            self.retry()
        else:
            update_task(kwargs['task_id'])
        return result
    except Exception as exc:
        self.retry(exc=exc)


from .my_lib.tourico.tourico_func import queryGetHotelDetailsV3, get_per_data, insert_data as tourico_insert_data


@app.task(bind=True, base=BaseTask, max_retries=10, rate_limit='15/s')
def tourico_base_data(self, hotel_id, city_id):
    try:
        hotels = queryGetHotelDetailsV3([hotel_id])
        data = get_per_data(hotels, city_id)
        if not data:
            self.retry()
        print tourico_insert_data([data])
    except:
        self.retry()


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='15/s')
def get_images_without_md5(self, source, target_url):
    # PROXY = get_proxy(source="Platform")
    # proxies = {
    #     'http': 'socks5://' + PROXY,
    #     'https': 'socks5://' + PROXY
    # }
    headers = {
        'User-agent': GetUserAgent()
    }
    try:
        page = requests.get(target_url, headers=headers, timeout=480)
        f = StringIO(page.content)
        flag, h, w = is_complete_scale_ok(f)
        if flag in [1, 2]:
            # x = time.time()
            # update_proxy('Platform', PROXY, x, '22')
            # print "Image Error with Proxy " + PROXY
            self.retry(countdown=2)
        else:
            # x = time.time()
            # print "Success with " + PROXY + ' CODE 0'
            file_name = target_url.split('/')[-1].split('.')[0]
            save_image(source, file_name, page.content)
            # update_proxy('Platform', PROXY, x, '0')
        return flag, h, w
    except Exception as exc:
        # x = time.time()
        # update_proxy('Platform', PROXY, x, '22')
        self.retry(exc=exc, countdown=2)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def get_images_without_md5_and_proxy(self, source, target_url):
    try:
        page = requests.get(target_url, timeout=360)
        f = StringIO(page.content)
        flag, h, w = is_complete_scale_ok(f)
        if flag in [1, 2]:
            self.retry(countdown=2)
        else:
            file_name = target_url.split('/')[-1].split('.')[0]
            save_image(source, file_name, page.content)
        return flag, h, w
    except Exception as exc:
        self.retry(exc=exc, countdown=2)


from .my_lib.tourico.tourico_city_func import queryGetHotelsByDestination, get_hotel_id, insert_hotel_id


@app.task(bind=True, base=BaseTask, max_retries=10, rate_limit='15/s')
def tourico_hotel_id(self, continent_name, country_name, state_name, city_name):
    try:
        res = queryGetHotelsByDestination(continent_name, country_name, state_name, city_name)
        try:
            hotel_id_list, city_map = get_hotel_id(res)
        except:
            self.retry()
        datas = []
        for h_id in hotel_id_list:
            data = (str(h_id), continent_name, country_name, state_name, city_name, city_map, '0')
            datas.append(data)
        print insert_hotel_id(datas)
        # if datas:
        #     print insert_finished_city((continent_name, country_name, state_name, city_name))
    except:
        print "ERROR", continent_name, country_name, state_name, city_name
        self.retry()


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='15/s')
def booking_comment_without_proxy(self, target_url):
    headers = {
        'User-agent': GetUserAgent()
    }
    try:
        page = requests.get(target_url, headers=headers, timeout=120)
        page.encoding = 'utf8'
        result = booking_comment_parser(page.text, target_url)
        if not result:
            self.retry()
        return result
    except Exception as exc:
        self.retry(exc=exc)


@app.task(bind=True, base=BaseTask, max_retries=10)
def get_images_info(self, path):
    try:
        flag, h, w = is_complete_scale_ok(path)
        print db_localhost.ExecuteSQL(sql='insert into image_info (`file_name`,`file_info`) VALUES (%s,%s)',
                                      args=(path.split('/')[-1] + '_flag', '###'.join([str(flag), str(h), str(w)])))
        return flag, h, w
    except Exception as exc:
        self.retry(exc=exc, countdown=5)


import hashlib
import redis
import shutil
from .my_lib.hotel_img_func import insert_db as hotel_images_info_insert_db, get_file_md5
from pymysql.err import IntegrityError

redis_dict = redis.Redis(host='10.10.180.145', db=5)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='14/s')
def get_hotel_images_info(self, path, part, desc_path, **kwargs):
    try:
        print 'Get File',
        if os.path.getsize(path) > 10485760:
            raise Exception('Too Large')
        file_md5 = get_file_md5(path)
        flag, h, w = is_complete_scale_ok(path)
        # (`source`, `source_id`, `pic_url`, `pic_md5`, `part`, `size`, `flag`)
        pic_md5 = path.split('/')[-1]
        res_flag = 1 if flag == 0 else 0
        raw = redis_dict.get(pic_md5.replace('.jpg', ''))
        if not raw:
            print "Error Raw"
            self.retry()
        source, sid, pic_url = raw.split('###')
        size = str((h, w))
        if size == '(-1, -1)':
            print "Error Size"
            self.retry()
        data = (
            source,  # source
            sid,  # source_id
            pic_url,  # pic_url
            pic_md5,  # pic_md5
            part,  # part
            size,  # size
            res_flag,  # flag
            file_md5  # file_md5
        )
        print 'Data', data
        try:
            print hotel_images_info_insert_db(data)
            shutil.copy(path, os.path.join(desc_path, pic_md5))
        except IntegrityError as err:
            pass
        print update_task(kwargs['task_id'])
        print 'Succeed'
        return flag, h, w
    except Exception as exc:
        print "Error Exception"
        self.retry(exc=exc, countdown=10)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='50/s')
def get_images_without_proxy(self, source, target_url, **kwargs):
    headers = {
        'User-agent': GetUserAgent()
    }
    try:
        print 'Get Img Url', target_url
        page = requests.get(target_url, headers=headers, timeout=240)
        f = StringIO(page.content)
        flag, h, w = is_complete_scale_ok(f)
        if flag in [1, 2]:
            print 'Img', target_url, 'Error in 1,2'
            self.retry(countdown=2)
        else:
            update_task(kwargs['task_id'])
            file_name = hashlib.md5(target_url).hexdigest()
            save_image(source, file_name, page.content)
            print source, file_name, 'success'
        return flag, h, w
    except Exception as exc:
        print 'Exception', str(exc)
        self.retry(exc=exc, countdown=2)


def qyer_img_parser(content):
    root = html.fromstring(content)
    for img_element in root.find_class('pla_photolist')[0].xpath('./li'):
        yield img_element.find_class('_jsbigphotoinfo')[0].xpath('./img/@src')[0].replace('180180', '980x576')


def qyer_img_insert_db(args):
    sql = 'insert into qyer_img (`mid`,`url`,`img_list`) VALUES (%s,%s,%s)'
    return db_localhost.ExecuteSQL(sql, args)


@app.task(bind=True, base=BaseTask, max_retries=10, rate_limit='15/s')
def qyer_img_task(self, target_url, mid):
    headers = {
        'User-agent': GetUserAgent()
    }
    try:
        page = requests.get(target_url, headers=headers, timeout=120)
        raw_img_result = '|'.join(qyer_img_parser(page.text))
        if not raw_img_result:
            self.retry()
            print "Fail", target_url
        else:
            qyer_img_insert_db((mid, target_url, raw_img_result))
            print "Succeed", target_url
        return raw_img_result
    except:
        print "Fail", target_url
        self.retry()


from .my_lib.switzerland.switzerland import switzerland_parser, update_db as switzerland_update_db


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='15/s')
def switzerland_task(self, target_url, m_id, m_type):
    try:
        res = switzerland_parser(target_url, m_id, m_type)
        if not res:
            self.retry()
            print "Fail", target_url
        else:
            switzerland_update_db(res)
            print "Succeed", target_url
        return res
    except:
        print "Fail", target_url
        self.retry()


from .my_lib.price_level.price_level import get_yelp_price_level, update_db as yelp_price_level_update_db


@app.task(bind=True, base=BaseTask, max_retries=15, rate_limit='15/s')
def yelp_price_level(self, target_url, mid):
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
        page = requests.get(target_url, proxies=proxies, headers=headers, timeout=120)
        price_level = get_yelp_price_level(page)
        if not page.text:
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            print "Success with " + PROXY + ' CODE 0'
            update_proxy('Platform', PROXY, x, '0')
            print yelp_price_level_update_db((price_level, mid))
        return price_level
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='360/s')
def get_lost_poi_image(self, file_path, file_name, target_url):
    headers = {
        'User-agent': GetUserAgent()
    }

    try:
        page = requests.get(target_url, headers=headers, timeout=480)
        f = StringIO(page.content)
        flag, h, w = is_complete_scale_ok(f)
        if flag in [1, 2]:
            self.retry(countdown=2)
        else:
            save_image(file_path, file_name, page.content)
        return flag, h, w
    except Exception as exc:
        self.retry(exc=exc, countdown=2)


def insert_daodao_image_list(args):
    sql = 'replace into daodao_img(`mid`,`url`,`img_list`) values (%s,%s,%s)'
    return db_localhost.ExecuteSQL(sql, args)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='30/s')
def get_daodao_image_url(self, source_url, mid, **kwargs):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }

    try:
        detail_id = re.findall('-d(\d+)', source_url)[0]
        target_url = 'http://www.tripadvisor.cn/LocationPhotoAlbum?detail=' + detail_id
        page = requests.get(target_url, proxies=proxies, headers=headers, timeout=240)
        page.encoding = 'utf8'
        if not page.text:
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            print "Success with " + PROXY + ' CODE 0'
            root = PyQuery(page.text)
            images_list = []
            for div in root('.photos.inHeroList div').items():
                images_list.append(div.attr['data-bigurl'])
            img_list = '|'.join(images_list)
            if img_list == '':
                self.retry()
            data = (mid, source_url, img_list)
            print insert_daodao_image_list(data)
            update_proxy('Platform', PROXY, x, '0')
            update_task(kwargs['task_id'])
        return data
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=exc)


def insert_crawled_html(args, table_name):
    conn = MySQLdb.connect(host='10.10.231.105', user='hourong', passwd='hourong', db='crawled_html', charset="utf8")
    with conn as cursor:
        sql = 'insert ignore into crawled_html.{0}(`md5`,`url`,`content`,`flag`) values (%s,%s,%s,%s)'.format(
            table_name)
        return cursor.execute(sql, args)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='40/s')
def craw_html(self, url, flag, table_name, **kwargs):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    md5_url = hashlib.md5(url).hexdigest()
    try:
        page = requests.get(url, proxies=proxies, headers=headers, timeout=240)
        page.encoding = 'utf8'
        if len(page.text) == 0:
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            print "Success with " + PROXY + ' CODE 0 takes ' + str(time.time() - x)
            content = page.text
            # test data
            j_data = json.loads(content)
            if j_data['status'] not in ['OK', 'ZERO_RESULTS']:
                raise Exception('Status:\t' + j_data['status'])
            data = (md5_url, url, content, flag)
            # print insert_crawled_html(data, table_name)
            conn = MySQLdb.connect(host='10.10.231.105', user='hourong', passwd='hourong', db='crawled_html',
                                   charset="utf8")
            with conn as cursor:
                sql = 'insert ignore into crawled_html.{0}(`md5`,`url`,`content`,`flag`) values (%s,%s,%s,%s)'.format(
                    table_name)
                print cursor.execute(sql, data)
            update_proxy('Platform', PROXY, x, '0')
            task_id = kwargs.get('task_id', '')
            if task_id != '':
                update_task(task_id=task_id)
        # return data
        return 'OK' + str(len(data))
    except Exception as exc:
        update_proxy('Platform', PROXY, x, '23')
        print "Error", exc, 'takes', str(time.time() - x)
        print traceback.print_exc()
        self.retry(exc=exc)


# add lost attr

attr_oa_pattern = re.compile('-oa(\d+)')


@app.task(bind=True, base=BaseTask, max_retries=7, rate_limit='15/s')
def tp_attr_city_page(self, city_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(city_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(city_url)
    for item in doc('.attractions.twoLines a').items():
        tp_attr_list_page_num.delay(item.attr.href, city_id, part)


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='15/s')
def tp_attr_list_page_num(self, index_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(index_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(index_url)
    num_list = []
    for item in doc('.pageNumbers a').items():
        num = int(attr_oa_pattern.findall(item.attr.href)[0])
        num_list.append(num)

    tp_attr_detail_page_url.delay(index_url, city_id, part)
    try:
        for page_num in range(30, max(num_list) + 30, 30):
            tp_attr_detail_page_url.delay(index_url.replace('-Activities', '-Activities-oa' + str(page_num)), city_id,
                                          part)
    except:
        pass


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def tp_attr_detail_page_url(self, page_num_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(page_num_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(page_num_url)

    data = []
    worker = u'daodao_poi_base_data'
    for item in doc('.property_title a').items():
        href = item.attr.href
        if 'Attraction_Review' in href:
            args = json.dumps(
                {u'target_url': unicode(href), u'city_id': unicode(city_id), u'type': 'attr'})
            task_id = get_task_id(worker, args=args)
            data.append((task_id, worker, args, unicode(part).replace(u'list', u'detail')))
    print insert_task(data=data)


# add lost rest

rest_oa_pattern = re.compile('-oa(\d+)')
rest_g_pattern = re.compile('-g(\d+)')


@app.task(bind=True, base=BaseTask, max_retries=7, rate_limit='15/s')
def tp_rest_city_page(self, city_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(city_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(city_url)
    for item in doc('.restaurants.twoLines a').items():
        tp_rest_list_page_num.delay(item.attr.href, city_id, part)


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='15/s')
def tp_rest_list_page_num(self, index_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(index_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    page.encoding = 'utf8'
    doc = PyQuery(page.text)
    doc.make_links_absolute(index_url)
    num_list = []
    for item in doc('.pageNumbers a').items():
        num = int(rest_oa_pattern.findall(item.attr.href)[0])
        num_list.append(num)

    tp_rest_detail_page_url.delay(index_url, city_id, part)
    try:
        for page_num in range(30, max(num_list) + 30, 30):
            g_num = rest_g_pattern.findall(index_url)[0]
            tp_rest_detail_page_url.delay(index_url.replace('-g' + g_num, '-g{0}-oa{1}'.format(g_num, page_num)),
                                          city_id, part)
    except:
        pass


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def tp_rest_detail_page_url(self, page_num_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(page_num_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(page_num_url)

    data = []
    worker = u'daodao_poi_base_data'

    for item in doc('.property_title').items():
        href = item.attr.href
        if 'Restaurant_Review' in href:
            args = json.dumps(
                {u'target_url': unicode(href), u'city_id': unicode(city_id), u'type': u'rest'})
            task_id = get_task_id(worker, args=args)
            data.append((task_id, worker, args, unicode(part).replace(u'list', u'detail')))
    print insert_task(data=data)


@app.task(bind=True, base=BaseTask, max_retries=7, rate_limit='15/s')
def tp_shop_city_page(self, city_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(city_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(city_url)
    for item in doc('.attractions.twoLines a').items():
        tp_shop_shop_city_page.delay(item.attr.href, city_id, part)


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='15/s')
def tp_shop_shop_city_page(self, city_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(city_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(city_url)
    for item in doc('#ATTR_CATEGORY_26 a').items():
        tp_shop_list_page_num.delay(item.attr.href, city_id, part)


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='15/s')
def tp_shop_list_page_num(self, index_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(index_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(index_url)
    num_list = []
    for item in doc('.pageNumbers a').items():
        num = int(attr_oa_pattern.findall(item.attr.href)[0])
        num_list.append(num)

    tp_shop_detail_page_url.delay(index_url, city_id, part)
    try:
        for page_num in range(30, max(num_list) + 30, 30):
            tp_shop_detail_page_url.delay(index_url.replace('-Activities-c26', '-Activities-c26-oa' + str(page_num)),
                                          city_id, part)
    except:
        pass


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def tp_shop_detail_page_url(self, page_num_url, city_id, part):
    PROXY = get_proxy(source="Platform")
    x = time.time()
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent()
    }
    page = requests.get(page_num_url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    if len(page.text) < 100:
        update_proxy('Platform', PROXY, x, '23')
        self.retry()
    doc = PyQuery(page.text)
    doc.make_links_absolute(page_num_url)

    data = []
    worker = u'daodao_poi_base_data'

    for item in doc('.property_title a').items():
        href = item.attr.href
        if 'Attraction_Review' in href:
            args = json.dumps(
                {u'target_url': unicode(href), u'city_id': unicode(city_id), u'type': u'shop'})
            task_id = get_task_id(worker, args=args)
            data.append((task_id, worker, args, unicode(part).replace(u'list', u'detail')))
    print insert_task(data=data)


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='24/m')
def vote(self):
    import httplib
    httplib.HTTPConnection.debuglevel = 1
    httplib.HTTPSConnection.debuglevel = 1
    PROXY = get_proxy(source="Platform")
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    print "Now Proxy is " + PROXY
    headers = {
        'User-agent': GetUserAgent(),
        'Referer': 'http://www.travelmeetingsawards-china.com/Events/Awards2015Business/Readers-Voting/?cat=5',
        'Host': 'www.travelmeetingsawards-china.com',
        'Origin': 'http://www.travelmeetingsawards-china.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        # 'Cookie': 'EktGUID=91ea164d-e2c6-4748-8e31-33c05e6e5439; EkAnalytics=0; ASP.NET_SessionId=piy2livrdw4nb4vulygiet4y; awardvotes=[{"AwardEventID":7,"AwardCategoryID":5,"AwardSubCategoryID":98,"Datetime":"\/Date(1492764048212)\/"}]; s_cc=true; s_nr=1492766246608-New; _ga=GA1.2.1289463038.1492764050; _gat=1; ecm=user_id=0&isMembershipUser=0&site_id=&username=&new_site=/&unique_id=0&site_preview=0&langvalue=0&DefaultLanguage=2052&NavLanguage=2052&LastValidLanguageID=2052&DefaultCurrency=840&SiteCurrency=840&ContType=&UserCulture=1033&dm=www.travelmeetingsawards-china.com&SiteLanguage=2052; s_sq=ntmntmmcchina%3D%2526pid%253D(5105)%252520%2525E8%2525AF%2525BB%2525E8%252580%252585%2525E6%25258A%252595%2525E7%2525A5%2525A8%252520-%2525202017%2525E4%2525B8%2525AD%2525E5%25259B%2525BD%2525E6%252597%252585%2525E6%2525B8%2525B8%2525E4%2525B8%25259A%2525E7%252595%25258C%2525E5%2525A5%252596%2525EF%2525BC%252588%2525E5%252595%252586%2525E5%25258A%2525A1%2525E7%2525B1%2525BB%2525EF%2525BC%252589%2525E8%2525AF%252584%2525E9%252580%252589%252520%25257C%2526pidt%253D1%2526oid%253DVote%252520%2525E6%25258A%252595%2525E7%2525A5%2525A8%2526oidt%253D3%2526ot%253DSUBMIT'
    }

    # data = {
    #   '__VIEWSTATE': '/wEPDwUKLTQ0MDg4MzI3MWRkhc6az5DCGMMce+MYab5BPdm3oOCc0QhMXjgPO+KlHJc=',
    #    '__VIEWSTATEGENERATOR': 'C57773B4',
    #    '__EVENTVALIDATION': '/wEdAApdhN7azgIf7udjNG5rBO36uJWyBmoVrn+KGuzxsc+IdAhrj7iGCUNTOfLFH3a+X2zXZyb9ZhM4Agf2PTEzU0NRt9vByiAtAO532pQGgxLMkPxQ4KIC5CcITHzHErIOKsL+X/4YFsqB/WKj97Ohz20ZIOo7mLBzjoLYCKAW/gNPwcKu4LFvmYccMsvGxcqsoFFypiSNmMf2UIdcHp3gKJUE1+/bEdftTH+meRV6Ro2Ps7Lou2EFvxJCcav33eyACAc=',
    #    'ctl00$cphMain$ucVoting$rptVotingList$ctl02$rptTopThreeList$ctl02$btnVote': 'Vote 投票'
    # }
    data = {
        '__VIEWSTATE': '/wEPDwUKLTQ0MDg4MzI3MWRkhc6az5DCGMMce+MYab5BPdm3oOCc0QhMXjgPO+KlHJc=',
        '__VIEWSTATEGENERATOR': 'C57773B4',
        '__EVENTVALIDATION': '/wEdAApdhN7azgIf7udjNG5rBO36uJWyBmoVrn+KGuzxsc+IdAhrj7iGCUNTOfLFH3a+X2zXZyb9ZhM4Agf2PTEzU0NRt9vByiAtAO532pQGgxLMkPxQ4KIC5CcITHzHErIOKsL+X/4YFsqB/WKj97Ohz20ZIOo7mLBzjoLYCKAW/gNPwcKu4LFvmYccMsvGxcqsoFFypiSNmMf2UIdcHp3gKJUE1+/bEdftTH+meRV6Ro2Ps7Lou2EFvxJCcav33eyACAc=',
        'ctl00$cphMain$ucVoting$rptVotingList$ctl02$rptTopThreeList$ctl00$btnVote': 'Vote 投票'
    }
    session = requests.session()
    session.proxies = proxies
    session.headers.update(headers)
    ip_page = requests.get('https://api.ipify.org?format=json', proxies=proxies)
    out_ip = json.loads(ip_page.text)['ip']
    page = session.get('http://www.travelmeetingsawards-china.com/Events/Awards2015Business/Readers-Voting/?cat=5')
    page = session.post('http://www.travelmeetingsawards-china.com/Events/Awards2015Business/Readers-Voting/?cat=5',
                        data=data)
    save_ip(out_ip, PROXY)
    return out_ip


@app.task(bind=True, max_retries=3)
def save_ip(self, ip_address, local_proxy):
    conn = pymysql.connect(host='10.10.180.145', user='hourong', password='hourong', charset='utf8', db='IP')
    with conn as cursor:
        cursor.execute('INSERT INTO ip_used (`ip_address`, `local_proxy`) VALUES (%s, %s)', (ip_address, local_proxy))
    conn.close()
