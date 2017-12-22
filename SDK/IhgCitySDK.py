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
        with MySession(need_proxies=True, need_cache=True) as session:
            keyword = self.task.kwargs['keyword']
            suggest = {}
            try:
                response = session.get(
                    url=search_url,
                    headers=headers,
                    params={
                        'country': 'cn',
                        'language': 'zh',
                        'brand': 'ihg',
                        'query': keyword
                    }
                )

                json_data = json.loads(response.content)
                suggest['suggest'] = json_data
                db = client['SuggestName']
                db.IhgCitySuggest.save(suggest)
                self.task.error_code = 0
                return {'搜索到的suggest数量': json_data['preFilterCount']}
            except requests.exceptions.RequestException as e:
                raise ServiceStandardError(ServiceStandardError.PROXY_INVALID, wrapped_exception=e)
            except pymongo.errors.PyMongoError as e:
                raise ServiceStandardError(ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)
            except Exception as e:
                raise ServiceStandardError(ServiceStandardError.UNKNOWN_ERROR, wrapped_exception=e)


if __name__ == "__main__":
    args = {
        'keyword': 'Seoul'
    }
    task = Task(_worker='', _task_id='demo', _source='ihg', _type='poi_list', _task_name='ihg_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    ihg = IhgCitySDK(task)

    ihg.execute()
