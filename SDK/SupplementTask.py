#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/22 下午10:10
# @Author  : Hou Rong
# @Site    : 
# @File    : SupplementTask.py
# @Software: PyCharm

# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
import json
import re
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.Common.NetworkUtils import google_get_map_info,map_info_get_google
from proj.mysql_pool import service_platform_pool
from proj.my_lib.attr_parser import image_parser as attr_image_parser
from proj.my_lib.rest_parser import image_parser as rest_image_parser
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.ServiceStandardError import ServiceStandardError

update_map_info = "update %s set map_info='%s' where source='%s' and {field}='%s'"
update_status = "update supplement_field set status=%d where source='%s' and sid='%s' and type='map_info' and table_name='%s'"
update_imgurl = "update %s set imgurl='%s' where source='%s' and id='%s'"


def execute_sql(sql):
    service_platform_conn = service_platform_pool.connection()
    cursor = service_platform_conn.cursor()
    cursor.execute(sql, [])
    service_platform_conn.commit()
    cursor.close()
    service_platform_conn.close()


class SupplementMapInfo(BaseSDK):
    def _execute(self, **kwargs):
        table_name = self.task.kwargs['table_name']
        source = self.task.kwargs['source']
        sid = self.task.kwargs['sid']
        other_info = self.task.kwargs['other_info']

        address = json.loads(other_info).get('address').encode('utf8')
        if not address:
            execute_sql(update_status % (2, source, sid, table_name))
            raise ServiceStandardError(error_code=ServiceStandardError.KEY_WORDS_FILTER,
                                       wrapped_exception=Exception(u'address 为空'))

        map_info = google_get_map_info(address)
        if not map_info:
            execute_sql(update_status % (2, source, sid, table_name))
            raise ServiceStandardError(error_code=ServiceStandardError.KEY_WORDS_FILTER,
                                       wrapped_exception=Exception(u'mapinfo 为空'))

        sql = update_map_info % (table_name, map_info, source, sid)
        typ2 = table_name.split('_')[1]
        sql = sql.format(field='source_id' if typ2 == 'hotel' else 'id')

        execute_sql(sql)
        execute_sql(update_status % (1, source, sid, table_name))

        self.task.error_code = 0
        return source, sid


class SupplementDaodaoImg(BaseSDK):
    def _execute(self, **kwargs):
        table_name = self.task.kwargs['task_name']
        source = self.task.kwargs['source']
        sid = self.task.kwargs['sid']
        url = self.task.kwargs['url']

        typ2 = table_name.split('_')[1]
        try:
            source_id = re.compile(r'd(\d+)').findall(url)[0]
            if not source_id:
                raise ServiceStandardError(error_code=ServiceStandardError.PARSE_ERROR)
        except Exception as e:
            raise ServiceStandardError(
                error_code=ServiceStandardError.PARSE_ERROR,
                wrapped_exception=Exception('can not find source_id, url    %s' % url)
            )

        if typ2 == 'attr':
            img_url = attr_image_parser(source_id)
        elif typ2 == 'rest':
            img_url = rest_image_parser(source_id)
        else:
            img_url = None
        if not img_url:
            raise ServiceStandardError(error_code=ServiceStandardError.EMPTY_TICKET)
        sql = update_imgurl % (table_name, img_url, source, sid)
        execute_sql(sql)

        self.task.error_code = 0
        return source, sid

class SupplementReMapInfo(BaseSDK):
    def _execute(self, **kwargs):
        data = self.task.kwargs['data']
        code = map_info_get_google(data)
        if code == 'ok':
            self.task.error_code = 0
        return 'ok'

