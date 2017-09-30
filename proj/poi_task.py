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
from proj.my_lib.ServiceStandardError import TypeCheckError
from proj.my_lib.Common.KeyMatch import key_is_legal
from proj.my_lib.Common.Utils import google_get_map_info

from sqlalchemy.sql import text
import datetime

logger = get_logger("POIDetail")

parser_type = {
    'attr': attr_parser,
    'rest': rest_parser,
    'shop': shop_parser
}


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def get_lost_poi(self, target_url, city_id, poi_type, country_id, **kwargs):
    # TODO 入库处理未指定
    self.task_source = 'Daodao'
    self.task_type = 'DaodaoDetail'
    self.error_code = 103
    target_url = target_url.replace('.com.hk', '.cn')
    with MySession(need_cache=True) as session:
        page = session.get(target_url, timeout=15)
        page.encoding = 'utf8'

        parser = parser_type[poi_type]
        result = parser(page.content, target_url, city_id=city_id)

        if result == 'Error':
            self.error_code = 27
            raise Exception('parse %s Error' % target_url)

        result['city_id'] = city_id
        result['utime'] = datetime.datetime.now()
        sql_key = result.keys()

        retry_count = kwargs['retry_count']

        name = result['name']
        if name.find('停业') > -1:
            self.error_code = 109
            return self.error_code
        name_en = result['name_en']
        map_info = result['map_info']
        address = result['address']

        if not key_is_legal(map_info):
            if retry_count > 3:
                if not key_is_legal(address):
                    raise TypeCheckError(
                        'Error map_info and address NULL        with parser %ss    url %s' % (
                            parser.func_name, target_url))
                google_map_info = google_get_map_info(address)
                if not key_is_legal(google_map_info):
                    raise TypeCheckError(
                        'Error google_map_info  NULL        with parser %ss    url %s' % (parser.func_name, target_url))
                result['map_info'] = google_map_info
            else:
                raise TypeCheckError(
                    'Error map_info NULL        with parser %ss    url %s' % (parser.func_name, target_url))

        if key_is_legal(name) or key_is_legal(name_en):
            logger.info(name + '  ----------  ' + name_en)
        else:
            raise TypeCheckError(
                'Error name and name_en Both NULL        with parser %s    url %s' % (
                    parser.func_name, target_url))

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
