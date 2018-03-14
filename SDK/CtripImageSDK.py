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
logger = get_logger('ctripPoi_image')

client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
db = client['data_result']


class CtripCitySDK(BaseSDK):
    def _execute(self, **kwargs):
        with MySession(need_proxies=True, need_cache=True) as session:
            search_url = self.task.kwargs['url']
            try:
                response = session.get(
                    url=search_url
                )
                content = response.content
                datas = json.loads(content)
                for data in datas:
                    db.ctripPoi_image_url.insert_one(
                        data
                    )

                self.task.error_code = 0
                return {'搜索到的city数量': len(content)}
            except requests.exceptions.RequestException as e:
                raise ServiceStandardError(ServiceStandardError.PROXY_INVALID, wrapped_exception=e)
            except pymongo.errors.PyMongoError as e:
                raise ServiceStandardError(ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)
            except Exception as e:
                raise ServiceStandardError(ServiceStandardError.UNKNOWN_ERROR, wrapped_exception=e)


if __name__ == "__main__":
    args = {
        'url':'http://you.ctrip.com/Destinationsite/TTDSecond/Photo/AjaxPhotoDetailList?districtId=236&type=5&pindex=1&resource=15861',
    }
    task = Task(_worker='', _task_id='demo', _source='ctrip', _type='poi_list', _task_name='ctrip_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    ihg = CtripCitySDK(task)

    ihg.execute()
