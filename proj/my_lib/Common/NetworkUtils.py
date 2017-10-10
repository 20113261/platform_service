#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/9 下午2:06
# @Author  : Hou Rong
# @Site    : ${SITE}
# @File    : NetworkUtils.py
# @Software: PyCharm
import json
from urllib import quote

import proj.my_lib.Common.Browser
from proj.my_lib.Common.Utils import Coordinate
from proj.my_lib.logger import get_logger

logger = get_logger("google map_info logger")


def google_get_map_info(address):
    for i in range(4):
        try:
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
        except Exception as exc:
            logger.exception(msg="[crawl with exception]", exc_info=exc)
    return None
