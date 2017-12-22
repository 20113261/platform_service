#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pymongo
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Task import Task
import json
config = {
    'host': '10.10.213.148',
}

logger = get_logger('accor_suggest')

client = pymongo.MongoClient(**config)
db = client['SuggestName']

search_url = "http://book.accorhotels.cn/Intellisense/Search"

headers = {
    "Cookie": "NSC_10.10.10.244-80=ffffffff090214e145525d5f4f58455e445a4a423660; language=zh-CN",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
}

class AccorCitySDK(BaseSDK):

    def _execute(self, **kwargs):
        with MySession(need_proxies=True,need_cache=True,auto_update_host=True) as session:
            keyword = self.task.kwargs['keyword']
            suggest = {}
            try:
                response = session.post(
                    url=search_url,
                    headers=headers,
                    data={
                        'searchText': keyword
                    }
                )

                json_data = json.loads(response.content)
                suggest['suggest'] = json_data
                db = client['SuggestName']
                db.AccorCitySuggest.save(suggest)
            except Exception as e:
                raise ServiceStandardError(ServiceStandardError.REQ_ERROR,wrapped_exception=e)
            except Exception as e:
                raise ServiceStandardError(ServiceStandardError.MYSQL_ERROR,wrapped_exception=e)
        self.task.error_code = 0
        return {'搜索到的suggest数量': json_data['TotalItemsCount']}

if __name__ == "__main__":
    args = {
        'keyword': 'paris'
    }
    task = Task(_worker='', _task_id='demo', _source='accor', _type='poi_list', _task_name='ihg_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    ihg = AccorCitySDK(task)

    ihg.execute()