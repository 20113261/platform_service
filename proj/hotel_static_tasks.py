#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/20 上午9:58
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_static_tasks.py
# @Software: PyCharm

# coding=utf-8
import sys

reload(sys)
sys.setdefaultencoding('utf8')

from .celery import app
from .my_lib.new_hotel_parser.hotel_parser import parse_hotel
from .my_lib.task_module.task_func import update_task
from .my_lib.BaseTask import BaseTask
from .my_lib.PageSaver import get_page_content


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='50/s')
def hotel_static_base_data(self, parent_task_id, task_name, source, source_id, city_id, hotel_url, **kwargs):
    try:
        # 获取保存的页面信息
        other_info = {
            'source_id': source_id,
            'city_id': city_id
        }
        result = parse_hotel(
            content=get_page_content(task_id=parent_task_id, task_name=task_name),
            url=hotel_url,
            other_info=other_info,
            source=source,
            part=task_name
        )

        if not result:
            self.retry(exc=Exception('db error'))
        else:
            if kwargs.get('task_id'):
                update_task(kwargs['task_id'])
            print "Success CODE 0"
        return result
    except Exception as exc:
        self.retry(exc=exc)
