#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/24 上午9:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm

import traceback
import datetime
import json
import hashlib
import pymysql

from send_task import hourong_patch

def qyer_supplement_map_info(tasks):
    data = []
    utime = None
    success_count = 0
    for table_name, type, source, sid, other_info, status, utime in tasks:
        if source!='qyer':continue
        task_info = {
            'worker': 'proj.supplement_mapinfo_task.supplement_map_info',
            'queue': 'supplement_field',
            'routing_key': 'supplement_field',
            'task_name': 'supplement_qyer_map_info',
            'args': {
                'table_name': table_name,
                'source': source,
                'sid': sid,
                'other_info': other_info,
            },#table_name, source, sid, other_info
            'priority': 3,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
        data.append(task_info)

        try:
            success_count += hourong_patch(data)
            data = []
        except Exception as exc:
            print '==========================0======================='
            # print source_id, city_id
            print traceback.format_exc(exc)
            print '==========================1======================='
    else:
        if len(data)>0:
            success_count += hourong_patch(data)

    return utime, success_count