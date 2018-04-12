#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/21 下午8:14
# @Author  : Hou Rong
# @Site    : 
# @File    : CrawlJson.py
# @Software: PyCharm
import json
# import base64
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.BaseSDK import BaseSDK
# from toolbox.Hash import encode
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.GoogleRealTraffic.parseData import ParseGoogleData
from proj.my_lib.GoogleRealTraffic.insert_rabbitmq import insert_rabbitmq


class GoogleDriveSDK(BaseSDK):
    def _execute(self, **kwargs):
        url = self.task.kwargs['url']
        task_id = self.task.kwargs['task_id']
        # md5_url = encode(url)
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

                result = dict()
                pdata, index_key, info_key = ParseGoogleData(
                    url=url,
                    data=content
                )
                result["url"] = url
                result["para"] = pdata
                result["index_key"] = index_key
                result["info_key"] = info_key
                # result["coor_key"] = coor_key
                result["task_id"] = str(task_id)

                try:
                    insert_rabbitmq(args=result)
                except Exception as e:
                    raise ServiceStandardError(error_code=ServiceStandardError.RABBITMQ_ERROR, wrapped_exception=e)
            self.task.error_code = 0
            return 'OK', url
