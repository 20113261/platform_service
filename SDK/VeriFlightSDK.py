#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/1/11 下午6:34
# @Author  : Hou Rong
# @Site    : 
# @File    : VeriFlightSDK.py
# @Software: PyCharm
import json
import pymongo
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.Utils import retry
from proj.config import MONGO_DATA_URL

logger = get_logger("VeriFlightSDK")
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
}
client = pymongo.MongoClient(MONGO_DATA_URL)
data_collections = client['Data']['veriflight']


class VeriFlightSDK(BaseSDK):
    @retry(times=5)
    def _execute(self, **kwargs):
        with MySession(need_cache=True, need_proxies=True) as session:
            iata_code = self.task.kwargs['iata_code']
            request_body = {
                "union": "",
                "maker": "",
                "isStop": "0",
                "isDomestic": "1",
                "isCross": "1",
                "queryDate2": "",
                "ftype": "",
                "queryDate1": "",
                "dep": iata_code,
                "isShare": "0",
                "depType": "1",
            }
            response = session.post(
                url="http://map.variflight.com/___api/SuXAvAQ0qWkchQuUUqHN/de1",
                headers=headers,
                data=request_body
            )

            try:
                data = json.loads(response.text)
                if int(data['code']) != 0:
                    raise ServiceStandardError(error_code=ServiceStandardError.PROXY_FORBIDDEN)

                data_collections.save(
                    {
                        'iata_code': iata_code,
                        'data': data
                    }
                )

            except Exception as e:
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)
        self.task.error_code = 0
        return data
