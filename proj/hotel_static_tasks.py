#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/20 上午9:58
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_static_tasks.py
# @Software: PyCharm

# coding=utf-8
import sys
import traceback

reload(sys)
sys.setdefaultencoding('utf8')

from proj.celery import app
from proj.my_lib.new_hotel_parser.hotel_parser import parse_hotel
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.PageSaver import get_page_content
from my_lib.new_hotel_parser.data_obj import DBSession

from proj.my_lib.logger import get_logger

logger = get_logger("HotelTripadvisor")


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='5/s')
def hotel_static_base_data(self, parent_task_id, task_name, source, source_id, city_id, hotel_url, **kwargs):
    self.task_source = source.title()
    self.task_type = 'HotelStaticDataParse'
    # 获取保存的页面信息
    other_info = {
        'source_id': source_id,
        'city_id': city_id
    }
    logger.info(
        'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_tripadvisor_total_new&id=' + parent_task_id)
    result = parse_hotel(
        content=get_page_content(task_id=parent_task_id, task_name=task_name),
        url=hotel_url,
        other_info=other_info,
        source=source,
        part=task_name
    )

    if not result:
        raise Exception('db error')

    try:
        # logger.info(str(result))
        session = DBSession()
        session.merge(result)
        session.commit()
        session.close()
    except Exception as e:
        self.error_code = 33
        logger.exception(e)
        raise e

    self.error_code = 0
    return result
