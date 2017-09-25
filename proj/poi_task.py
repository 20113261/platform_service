#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from proj.celery import app
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.PageSaver import save_task_and_page_content
from proj.my_lib.rest_parser import parse as rest_parser
from proj.my_lib.shop_parser import parse as shop_parser
from proj.my_lib.attr_parser import parse as attr_parser
from proj.my_lib.db_localhost import DBSession
from proj.my_lib.new_hotel_parser.data_obj import text_2_sql
from proj.my_lib.logger import get_logger

from sqlalchemy.sql import text
import datetime

logger = get_logger("POIDetail")

parser_type = {
    'attr': attr_parser,
    'rest': rest_parser,
    'shop': shop_parser
}


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def get_lost_poi(self, target_url, city_id, poi_type, country_id, **kwargs):
    # TODO 入库处理未指定
    self.task_source = 'Daodao'
    self.task_type = 'DaodaoDetail'
    self.error_code = 103
    target_url = target_url.replace('.com.hk', '.cn')
    with MySession(need_cache=True) as session:
        page = session.get(target_url, timeout=15)
        page.encoding = 'utf8'
        result = parser_type[poi_type](page.content, target_url, city_id=city_id)

        if result == 'Error':
            self.error_code = 27
            raise Exception('parse %s Error' % target_url)

        result['city_id'] = city_id
        result['utime'] = datetime.datetime.now()
        sql_key = result.keys()

        try:
            session = DBSession()
            session.execute(text(text_2_sql(sql_key).format(table_name=kwargs['task_name'])), [result])
            session.commit()
            session.close()
        except Exception as e:
            self.error_code = 33
            logger.exception(e)
            raise e

        self.error_code = 0
        return self.error_code
