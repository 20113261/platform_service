#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/9 下午2:06
# @Author  : Hou Rong
# @Site    : ${SITE}
# @File    : NetworkUtils.py
# @Software: PyCharm
import json
from urllib import quote

import pymongo
import proj.my_lib.Common.Browser
from proj.my_lib.Common.Utils import Coordinate
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.Utils import retry

logger = get_logger("google map_info logger")

client = pymongo.MongoClient('10.19.2.103:27017', 27017, username='root', password='miaoji1109-=')
db = client['Google_city']
col = db['mapGoogle']

@retry(times=4, raise_exc=False)
def google_get_map_info(address):
    with proj.my_lib.Common.Browser.MySession(need_cache=True) as session:
        page = session.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + quote(address))
        results = json.loads(page.text).get(
            'results', [])
        if len(results) == 0:
            raise Exception("length 0")

        map_info = results[0].get('geometry', {}).get('location', {})

        try:
            longitude = float(map_info.get('lng', None))
            latitude = float(map_info.get('lat', None))
        except Exception as e:
            raise e
        return str(Coordinate(longitude, latitude))


@retry(times=4, raise_exc=False)
def map_info_get_google(data):
    try:
        id = data.split('&')[0]
        map_info = data.split('&')[1]
        g_map = data.split('&')[1].split(',')[1] + ',' + data.split('&')[1].split(',')[0]
        url = "http://maps.google.cn/maps/api/geocode/json?latlng=" + g_map + "&language=ch_ZN"  # &key=AIzaSyAEW0pcYAcP8bBMOOJLIZvEuDbmadWXGG0"
        with proj.my_lib.Common.Browser.MySession(need_cache=True) as session:
            page = session.get(url)
            res = json.loads(page.text)
        if res['status'] == 'OK':
            res['id'] = id
            res['map_info'] = map_info
            col.insert(res)
            return 'ok'
        else:
            raise Exception('need retry')
    except Exception as e:
        raise e
