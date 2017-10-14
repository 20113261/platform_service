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
from proj.my_lib.attr_parser import image_parser as attr_image_parser
from proj.my_lib.rest_parser import image_parser as rest_image_parser

import json
import re

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

@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def supplement_map_info(self, table_name, source, sid, other_info, **kwargs):
    task_response = kwargs['task_response']
    task_response.source = source.title()
    task_response.type = 'SupplementField'

    address = json.loads(other_info).get('address').encode('utf8')
    if not address:
        execute_sql(update_status % (2, source, sid, table_name))
        raise Exception(u'address 为空')

    map_info = google_get_map_info(address)
    if not map_info:
        execute_sql(update_status % (2, source, sid, table_name))
        raise Exception(u'mapinfo 为空')

    sql = update_map_info % (table_name, map_info, source, sid)
    typ2 = table_name.split('_')[1]
    sql = sql.format(field='source_id' if typ2=='hotel' else 'id')

    execute_sql(sql)
    execute_sql(update_status % (1, source, sid, table_name))

    task_response.error_code = 0
    return source, sid


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='4/s')
def supplement_daodao_img(self, table_name, source, sid, url, **kwargs):
    task_response = kwargs['task_response']
    task_response.source = source.title()
    task_response.type = 'SupplementField'

    typ2 = table_name.split('_')[1]
    try:
        source_id = re.compile(r'd(\d+)').findall(url)[0]
        if not source_id:
            task_response.error_code = 27
            raise Exception
    except Exception as e:
        task_response.error_code = 27
        raise Exception('can not find source_id, url    %s' % url)

    if typ2=='attr':
        imgurl = attr_image_parser(source_id)
    elif typ2=='rest':
        imgurl = rest_image_parser(source_id)
    print imgurl
    if not imgurl:
        task_response.error_code = 27
        raise Exception('imgurl is None')
    sql = update_imgurl % (table_name, imgurl, source, sid)
    print sql

    execute_sql(sql)

    task_response.error_code = 0
    return source, sid

if __name__ == '__main__':
    # supplement_map_info('', 'detail_total_qyer_20170928a', 'qyer', '101904', '{"address": "Parsonage Gardens"}')
    # supplement_map_info('', 'detail_total_qyer_20170928a', 'qyer', '1201768', '{"address": "Lungarno Degli Acciaiuoli, 6-8/R"}')
    # supplement_daodao_img('', 'detail_attr_daodao_20170929a', 'daodao', '10005621', 'https://www.tripadvisor.cn//Attraction_Review-g298484-d10024357-Reviews-Church_of_The_Holy_Apostle_and_Evangelist_John_The_Theologian-Moscow_Central_Rus.html')
    # supplement_daodao_img('', 'detail_rest_daodao_20170929a', 'daodao', '10000025', 'https://www.tripadvisor.cn/Restaurant_Review-g1983013-d10000025-Reviews-Mexicanos-Markt_Indersdorf_Upper_Bavaria_Bavaria.html')
    # supplement_daodao_img('', 'detail_rest_daodao_20170929a', 'daodao', '1000321', 'https://www.tripadvisor.cn//Restaurant_Review-g187472-d1000321-Reviews-Tapa_en_Tapa-Las_Palmas_de_Gran_Canaria_Gran_Canaria_Canary_Islands.html')
    # supplement_daodao_img('', 'detail_attr_daodao_20170929a', 'daodao', '10670935', 'https://www.tripadvisor.cn//Attraction_Review-g1554295-d10670935-Reviews-Chiesa_di_San_Silvestro_I_Papa-Fanano_Province_of_Modena_Emilia_Romagna.html')
    supplement_daodao_img('', 'detail_attr_daodao_20170929a', 'daodao', '10000109', 'https://www.tripadvisor.cn//Attraction_Review-g55557-d10000109-Reviews-Off_Duty_Armory-Burleson_Texas.html')


