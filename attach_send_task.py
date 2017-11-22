#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/24 上午9:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from MongoTaskInsert import InsertTask


def qyer_supplement_map_info(tasks):
    utime = None
    _count = 0

    if not tasks:
        return utime

    source = tasks[0][0]
    with InsertTask(worker='proj.total_tasks.supplement_map_info', queue='supplement_field',
                    routine_key='supplement_field',
                    task_name='supplement_field', source=source.title(), _type='SupplementField',
                    priority=3) as it:
        for table_name, type, source, sid, other_info, status, utime in tasks:
            _count += 1
            it.insert_task({
                'table_name': table_name,
                'source': source,
                'sid': sid,
                'other_info': other_info,
            })

    return utime
