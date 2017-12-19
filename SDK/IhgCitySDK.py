#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pymongo
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
import json
config = {
    'host': '10.10.213.148',
}

logger = get_logger('ihg_suggest')

client = pymongo.MongoClient(**config)
db = client['SuggestName']

headers = {
    'referer': 'https://www.ihg.com/hotels/cn/zh/reservation',
    'x-requested-with': 'XMLHttpRequest',
    'accept-encoding': 'gzip, deflate, br',
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
}
search_url = "https://www.ihg.com/guestapi/v1/ihg/cn/zh/web/suggestions"

class IhgCitySDK(BaseSDK):

    def _execute(self, **kwargs):
        with MySession(need_proxies=True,need_cache=True,auto_update_host=True) as session:
            keyword = self.task.kwargs['keyword']
            suggest = {}
            response = session.get(
                url=search_url,
                headers =headers,
                params ={
                    'country': 'cn',
                    'language': 'zh',
                    'brand': 'ihg',
                    'query': keyword
                }
            )
            try:
                json_data = json.loads(response.content)
                suggest['suggest'] = json_data
                db = client['SuggestName']
                db.IngCitySuggest.save(suggest)
                db.IngCitySuggest.close()
            except Exception as e:
                raise ServiceStandardError(ServiceStandardError.MYSQL_ERROR,wrapped_exception=e)
        self.finished_error_code = 0
        return json_data['preFilterCount']




if __name__ == "__main__":
    pass