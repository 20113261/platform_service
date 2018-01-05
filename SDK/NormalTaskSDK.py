#!/usr/bin/env python
# -*- coding:utf-8 -*-

from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Task import Task
from SDK.IhgCitySDK import IhgCitySDK
from SDK.MarriottCitySDK import MarriottCitySDK
from SDK.BaiDuSearchSDK import BaiDuSearchSDK
from SDK.DaoDaoCitySDK import DaoDaoCitySDK


class NormalTaskSDK(BaseSDK):

    def get_task_sdk(self,source=None):
        all_sdk = {
             'marriott': MarriottCitySDK,
             'baidusearch': BaiDuSearchSDK,
             'daodao': DaoDaoCitySDK,
             'ihg': IhgCitySDK
        }
        class_name = None
        source = source.lower()
        for key in all_sdk.keys():
            if source in key:
                class_name = all_sdk.get(key)
                break
        return class_name

    def _execute(self, **kwargs):

        source = self.task.source
        class_name = self.get_task_sdk(source)
        sdk_object = class_name(self.task)
        sdk_object.execute()

if __name__ == "__main__":
    args = {
        'keyword': '纽约'
    }
    task = Task(_worker='', _task_id='demo', _source='daodao', _type='poi_list', _task_name='daodao_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    normal = NormalTaskSDK(task)

    normal.execute()