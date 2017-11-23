#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/25 下午10:30
# @Author  : Hou Rong
# @Site    : 
# @File    : qyer_detail_test.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import qyer_detail_task

if __name__ == '__main__':
    task = Task(_worker='', _task_id='demo', _source='qyer', _type='poi_detail',
                _task_name='detail_total_qyer_20171120a',
                _used_times=0, max_retry_times=6,
                # kwargs={'target_url': 'http://place.qyer.com/poi/V2UJYlFkBzVTbFI-/', 'city_id': 'TEST'},
                # kwargs={"city_id": "NULL", "part": "detail_total_qyer_20171120a",
                #         "target_url": "http://place.qyer.com/poi/V2wJZ1FgBzNTbA/"},
                kwargs={"city_id": "NULL", "part": "detail_total_qyer_20171120a",
                        "target_url": "http://place.qyer.com/poi/V2UJY1FnBzZTZFI5/"},
                _queue='poi_detail', _routine_key='poi_detail', task_type=0, list_task_token=''
                )
    qyer_detail_task(task=task)
