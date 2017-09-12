#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/26 下午10:42
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_routine_tasks.py
# @Software: PyCharm
# coding=utf-8
import re
from my_lib.new_hotel_parser.data_obj import DBSession
from proj.celery import app
from proj.my_lib.new_hotel_parser.hotel_parser import parse_hotel, TypeCheckError
from proj.my_lib.BaseRoutineTask import BaseRoutineTask
from proj.my_lib.PageSaver import save_task_and_page_content
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.logger import get_logger

logger = get_logger("HotelDetail")


@app.task(bind=True, base=BaseRoutineTask, max_retries=2, rate_limit='6/s')
def hotel_routine_base_data(self, source, url, other_info, **kwargs):
    self.task_source = source.title()
    self.task_type = 'Hotel'

    self.error_code = 0

    # 初始化任务
    try:
        # hotels
        if source == 'hotels':
            hotel_id = re.findall('hotel-id=(\d+)', url)[0]
            url = 'http://zh.hotels.com/hotel/details.html?hotel-id=' + hotel_id
    except Exception as e:
        self.error_code = 12
        logger.exception(e)
        raise e

    # 修改请求参数
    try:
        pass
    except Exception as e:
        self.error_code = 101
        logger.exception(e)
        raise e

    try:
        session = MySession()
        page = session.get(url, timeout=240)
        page.encoding = 'utf8'
        content = page.text
    except Exception as e:
        self.error_code = 22
        logger.exception(e)
        raise e

    try:
        result = parse_hotel(content=content, url=url, other_info=other_info, source=source, part="NULL")
    except TypeCheckError as e:
        self.error_code = 102
        logger.exception(e)
        raise e
    except Exception as e:
        self.error_code = 27
        logger.exception(e)
        raise e

    try:
        session = DBSession()
        session.merge(result)
        session.commit()
        session.close()
    except Exception as e:
        self.error_code = 33
        logger.exception(e)
        raise e

    try:
        # 保存抓取成功后的页面信息
        save_task_and_page_content(task_name='hotelinfo_routine_{0}'.format(source), content=content,
                                   task_id=kwargs['mongo_task_id'], source=source,
                                   source_id=other_info['source_id'],
                                   city_id=other_info['city_id'], url=url)
    except Exception as e:
        self.error_code = 104
        logger.exception(e)
        raise e
