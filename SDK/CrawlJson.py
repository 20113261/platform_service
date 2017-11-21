#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/21 下午8:14
# @Author  : Hou Rong
# @Site    : 
# @File    : CrawlJson.py
# @Software: PyCharm
import json
import pymysql
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.BaseSDK import BaseSDK
from toolbox.Hash import encode
from proj.my_lib.ServiceStandardError import ServiceStandardError


class CrawlJson(BaseSDK):
    def _execute(self, **kwargs):
        url = self.task.kwargs['url']
        flag = self.task.kwargs['flag']
        table_name = self.task.kwargs['table_name']

        md5_url = encode(url)
        with MySession(need_proxies=True, need_cache=True) as session:
            page = session.get(url, timeout=240)
            page.encoding = 'utf8'
            if len(page.text) == 0:
                raise ServiceStandardError(error_code=ServiceStandardError.PROXY_FORBIDDEN)
            else:
                content = page.text
                j_data = json.loads(content)
                if j_data['status'] not in ['OK', 'ZERO_RESULTS']:
                    raise ServiceStandardError(error_code=ServiceStandardError.PROXY_FORBIDDEN)

                data = (md5_url, url, content, flag)
                conn = pymysql.connect(host='10.10.231.105', user='hourong', passwd='hourong', db='crawled_html',
                                       charset="utf8")
                try:
                    with conn as cursor:
                        sql = 'insert ignore into crawled_html.{0}(`md5`,`url`,`content`,`flag`) values (%s,%s,%s,%s)'.format(
                            table_name)
                        print(cursor.execute(sql, data))
                except Exception as e:
                    raise ServiceStandardError(error_code=ServiceStandardError.PROXY_FORBIDDEN, wrapped_exception=e)
            self.task.error_code = 0
            return 'OK', url
