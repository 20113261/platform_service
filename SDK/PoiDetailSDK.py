#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from sqlalchemy.sql import text

from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.KeyMatch import key_is_legal
from proj.my_lib.Common.NetworkUtils import google_get_map_info
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.ServiceStandardError import TypeCheckError
from proj.my_lib.attr_parser import parse as attr_parser
from proj.my_lib.db_localhost import DBSession
from proj.my_lib.logger import get_logger
from proj.my_lib.new_hotel_parser.data_obj import text_2_sql
from proj.my_lib.rest_parser import parse as rest_parser
from proj.my_lib.shop_parser import parse as shop_parser

logger = get_logger("POIDetail")

parser_type = {
    'attr': attr_parser,
    'rest': rest_parser,
    'shop': shop_parser
}


class PoiDetailSDK(BaseSDK):
    def _execute(self, **kwargs):
        target_url = self.task.kwargs['target_url']
        city_id = self.task.kwargs['city_id']
        poi_type = self.task.kwargs['poi_type']

        target_url = target_url.replace('.com.hk', '.cn')
        with MySession(need_cache=True) as session:
            page = session.get(target_url, timeout=120)
            page.encoding = 'utf8'

            parser = parser_type[poi_type]
            result = parser(page.content, target_url, city_id=city_id)

            if result == 'Error':
                raise ServiceStandardError(ServiceStandardError.PARSE_ERROR)

            result['city_id'] = city_id
            # result['utime'] = datetime.datetime.now()
            sql_key = result.keys()

            name = result['name']
            # if name.find('停业') > -1:
            #     raise ServiceStandardError(error_code=ServiceStandardError.TARGET_CLOSED)
            name_en = result['name_en']
            map_info = result['map_info']
            address = result['address']

            map_info_is_legal = True
            try:
                lon, lat = map_info.split(',')
                if float(lon) == 0.0 and float(lat) == 0.0:
                    map_info_is_legal = False
            except Exception as e:
                map_info_is_legal = False
                logger.exception(msg="[map info is not legal]", exc_info=e)

            if not key_is_legal(map_info) or not map_info_is_legal:
                if not key_is_legal(address):
                    pass
                    # raise TypeCheckError(
                    #     'Error map_info and address NULL        with parser %ss    url %s' % (
                    #         parser.func_name, target_url))
                google_map_info = google_get_map_info(address)
                if not key_is_legal(google_map_info):
                    pass
                    # raise TypeCheckError(
                    #     'Error google_map_info  NULL  with [parser: {}][url: {}][address: {}][map_info: {}]'.format(
                    #         parser.func_name, target_url, address, map_info)
                    # )
                result['map_info'] = google_map_info
            if key_is_legal(name) or key_is_legal(name_en) or map_info_is_legal or key_is_legal(result.introduction):
                logger.info(name + '  ----------  ' + name_en)
            else:
                raise TypeCheckError(
                    'Error All Keys is None with parser %s  url %s' % (
                        parser.func_name, target_url))

            try:
                session = DBSession()
                session.execute(text(text_2_sql(sql_key).format(table_name=self.task.task_name)), [result])
                session.commit()
                session.close()
            except Exception as e:
                logger.exception(e)
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

            self.task.error_code = 0
            return self.task.error_code
