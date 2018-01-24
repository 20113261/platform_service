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


logger = get_logger('ctrip_suggest')

client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
db = client['SuggestName']

headers = {
    'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Host': 'www.tuniu.com',
    'Referer':'http://www.tuniu.com/tours/',
    'Cookie':'tuniuuser_citycode=MjAw'
}
search_url = "http://www.tuniu.com/tn"


class TuniuCitySDK(BaseSDK):
    def _execute(self, **kwargs):
        with MySession(need_proxies=True, need_cache=True) as session:
            keyword = self.task.kwargs['keyword']
            suggest = {}
            try:
                response = session.post(
                    url=search_url,
                    headers=headers,
                    params={'r':'search/search/searchSugguestV2',
                                'query':keyword,
                                'format':'json'}
                )
                content = response.content
                suggest['suggest'] = content
                db = client['SuggestName']
                db.TuniuCitySuggestion.save(suggest)
                self.task.error_code = 0
                return {'搜索到的city数量': 1}
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
    task = Task(_worker='', _task_id='demo', _source='tuniu', _type='poi_list', _task_name='tuniu_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    ihg = TuniuCitySDK(task)

    ihg.execute()
