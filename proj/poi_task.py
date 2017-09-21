#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.PageSaver import save_task_and_page_content
from proj.my_lib.rest_parser import parse as rest_parser
from proj.my_lib.shop_parser import parse as shop_parser
from proj.my_lib.attr_parser import parse as attr_parser

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
    with MySession() as session:
        page = session.get(target_url, timeout=15)
        page.encoding = 'utf8'
        result = parser_type[poi_type](page.content, target_url, city_id=city_id)
        save_task_and_page_content(task_name='daodao_poi_'+poi_type, content=page.content,
                                   task_id=kwargs['mongo_task_id'],
                                   source='daodao',
                                   source_id='NULL',
                                   city_id='NULL', url=target_url)

        if result == 'Error':
            raise Exception, 'parse %s Error' % target_url

        if not result['imgurl']:
            raise Exception('zhao bu dao tupian')
        result.country_id = country_id
        rest_insert_db(result, city_id)
        self.error_code = 0
        return result