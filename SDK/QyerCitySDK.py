#!/usr/bin/env python
# -*-coding:utf-8 -*-

from sqlalchemy.sql import text

from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.KeyMatch import key_is_legal
from proj.my_lib.Common.NetworkUtils import google_get_map_info
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.ServiceStandardError import TypeCheckError
from proj.my_lib.logger import get_logger
from proj.my_lib.my_qyer_parser.data_obj import DBSession
from proj.my_lib.my_qyer_parser.my_parser import page_parser
from proj.my_lib.new_hotel_parser.data_obj import text_2_sql
from proj.my_lib.Common.Utils import retry
import json
import pymongo

mongo_config = {
    'host': '10.10.213.148'
}
logger = get_logger("QyerPoiCity")

search_url = "http://www.qyer.com/qcross/home/ajax?action=search&keyword={0}"
headers = {
    "Referer": "http://www.qyer.com/",
    "Host": "www.qyer.com",
}
class QyerCitySDK(BaseSDK):

    @retry(times=5)
    def _execute(self, **kwargs):
        with MySession(need_cache=True, need_proxies=True) as session:
            keyword = self.task.kwargs['keyword']
            page = session.get(
                search_url.format(keyword),
                headers=headers,
                timeout=240
            )
            city_count = 0
            try:
                json_data = json.loads(page)
                client = pymongo.MongoClient(**mongo_config)
                db = client['SuggestName']

                db.QyerRawSuggest.save({'suggest': json_data})

                city_list = []
                citys = json_data.get('data', {}).get('list')
                for city in citys:
                    if city.get('type_name') == 'city':
                        city_count += 1
                        city_list.append(city)
                db.QyerCity.save({'city': city_list})
                client.close()
            except Exception as e:
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)
        self.task.error_code = 0
        return '抓取到的城市数量:%s' % city_count

