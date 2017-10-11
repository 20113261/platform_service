#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm

from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.Common.NetworkUtils import google_get_map_info
from proj.mysql_pool import service_platform_pool

import json

update_map_info = "update %s set map_info='%s' where source='%s' and {field}='%s'"
update_status = "update supplement_field set status=1 where source='%s' and sid='%s' and type='map_info' and table_name='%s'"

def execute_sql(sql):
    service_platform_conn = service_platform_pool.connection()
    cursor = service_platform_conn.cursor()
    cursor.execute(sql, [])
    service_platform_conn.commit()
    cursor.close()
    service_platform_conn.close()

@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def supplement_map_info(self, table_name, source, sid, other_info, **kwargs):
    task_response = kwargs['task_response']
    task_response.source = source.title()
    task_response.type = 'SupplementField'

    address = json.loads(other_info).get('address').encode('utf8')
    if not address:
        raise Exception('address 为空')

    map_info = google_get_map_info(address)
    if not map_info:
        raise Exception('mapinfo 为空')

    sql = update_map_info % (table_name, map_info, source, sid)
    typ2 = table_name.split('_')[1]
    sql = sql.format(field='source_id' if typ2=='hotel' else 'id')

    execute_sql(sql)
    execute_sql(update_status % (source, sid, table_name))

    task_response.error_code = 0
    return source, sid

if __name__ == '__main__':
    # supplement_map_info('', 'detail_total_qyer_20170928a', 'qyer', '101904', '{"address": "Parsonage Gardens"}')
    supplement_map_info('', 'detail_total_qyer_20170928a', 'qyer', '1201768', '{"address": "Lungarno Degli Acciaiuoli, 6-8/R"}')


