#!/usr/bin/env python
# -*- coding:utf-8 -*-
import pymongo
import pymongo.errors
import requests.exceptions
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Task import Task
import json
from lxml import html
config = {
    'host': '10.10.213.148',
}

logger = get_logger('marriott_suggest')

client = pymongo.MongoClient(**config)
db = client['SuggestName']

headers = {
    'referer': 'http://www.marriott.com.cn/default.mi',
    'x-requested-with': 'XMLHttpRequest',
    'accept-encoding': 'gzip, deflate, br',
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
}
search_url = "http://www.marriott.com.cn/search/autoComplete.mi"


class MarriottCitySDK(BaseSDK):
    def _execute(self, **kwargs):
        with MySession(need_proxies=True, need_cache=True) as session:
            keyword = self.task.kwargs['keyword']
            suggest = {}
            try:
                response = session.get(
                    url=search_url,
                    headers=headers,
                    params={
                        'searchType': 'InCity',
                        'applyGrouping': True,
                        'isWebRequest': True,
                        'searchTerm': keyword
                    }
                )

                content = response.content
                root = html.fromstring(content)
                city_list = root.xpath('//city')
                suggest['suggest'] = content
                db = client['SuggestName']
                db.MarriottCitySuggest.save(suggest)
                self.task.error_code = 0
                return {'搜索到的city数量': len(city_list)}
            except requests.exceptions.RequestException as e:
                raise ServiceStandardError(ServiceStandardError.PROXY_INVALID, wrapped_exception=e)
            except pymongo.errors.PyMongoError as e:
                raise ServiceStandardError(ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)
            except Exception as e:
                raise ServiceStandardError(ServiceStandardError.UNKNOWN_ERROR, wrapped_exception=e)


if __name__ == "__main__":
    args = {
        'keyword': '纽约'
    }
    task = Task(_worker='', _task_id='demo', _source='marriott', _type='poi_list', _task_name='marriott_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    ihg = MarriottCitySDK(task)

    ihg.execute()
