#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
@author: feng
@date: 18-01-31
'''
import pymongo
import pymongo.errors
import requests.exceptions
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Task import Task
import json

config = {
    'host': '10.10.213.148',
}

logger = get_logger('ctripPoi_suggest')

client = pymongo.MongoClient(**config)
db = client['SuggestName']

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
}
search_url = "http://you.ctrip.com/SearchSite/Service/Tip2"

class CtripPoiSDK(BaseSDK):

    def _execute(self, **kwargs):

        with MySession(need_proxies=True, need_cache=True) as session:
            keyword = self.task.kwargs['keyword']
            suggest = {}
            try:
                response = session.get(
                    url=search_url,
                    headers=headers,
                    data={
                        'Jsoncallback': 'jQuery',
                        'keyword': keyword
                    }
                )
                json_data = json.loads(response.content[7:-1])
                suggest['suggest'] = json_data
                db = client['SuggestName']
                db.CtripPoiSDK.save(suggest)
                self.task.error_code = 0
                count = 1
                if isinstance(json_data,list):
                    count = len(json_data)
                return {'搜索到的suggest数量': count}
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
    task = Task(_worker='', _task_id='demo', _source='ctirppoi', _type='poi_list', _task_name='ctrip_poi_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    normal = CtripPoiSDK(task)

    normal.execute()

