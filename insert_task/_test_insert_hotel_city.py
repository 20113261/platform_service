#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/20 下午4:18
# @Author  : Hou Rong
# @Site    : 
# @File    : insert_qyer_city.py
# @Software: PyCharm
import json
from data_source import MysqlSource
from my_logger import get_logger
from MongoTaskInsert import InsertTask, TaskType
from service_platform_conn_pool import source_info_config
from monitor import city2list

logger = get_logger("insert_mongo_task")


def get_tasks(source):
    # query_sql = '''SELECT *
    # FROM ota_location
    # WHERE source = '{}' AND city_id in ('11444','60177','12344','60178','10436','60179','60180','30118','30140','50053','60181','10648','11424','60182','60183','50117','20096');'''.format(
    #     source)

    # query_sql = '''SELECT *
    # FROM ota_location where source="{}"'''.format(source)

    query_sql = '''SELECT *
    FROM hilton_suggest_info where source="{}"'''.format(source)

    for _l in MysqlSource(db_config=source_info_config,
                          table_or_query=query_sql,
                          size=10000, is_table=False,
                          is_dict_cursor=True):
        yield _l


if __name__ == '__main__':

    source_list = ['hilton']

    for source in source_list:
        task_name = 'city_hotel_{}_20180531'.format(source)
        with InsertTask(worker='proj.total_tasks.zxp_hotel_list_task', queue='hotel_list', routine_key='list_hotel_hilton',
                        task_name=task_name, source=source.title(), _type='HotelList',
                        priority=11, task_type=TaskType.CITY_TASK) as it:
            for line in get_tasks(source=source):
                suggest = line['suggest']

                #holiday
                # args = {
                #     'source': source,
                #     'city_id': line['city_id'],
                #     'country_id': line['country_id'],
                #     'part': task_name.split('_')[-1],
                #     'is_new_type': 0,
                #     'suggest_type': line['suggest_type'],
                #     'suggest': suggest,
                #     # 'check_in': line['sid']
                # }

                #hyatt | shangrila
                # args = {
                #     "suggest" : "null",
                #     "country_id" : "null",
                #     "source" : "shangrila",
                #     "source_id" : "null",
                #     "city_id" : "null"
                # }

                #starwood
                # args = {
                #     "country_id" : line['country_id'],
                #     "source" : "gha",
                #     "suggest" : suggest,
                #     "city_id" : line['city_id'],
                #     "source_id" : line['sid']
                # }

                #gha
                # others_info = json.loads(line['others_info'], encoding=False)
                # city_id = others_info['href'] if others_info['href'] else ''
                # city = others_info['city'] if others_info['city'] else ''
                # country = others_info['country'] if others_info['country'] else ''
                # args = {
                #     "country_id": line['country_id'],
                #     "source": "gha",
                #     "suggest": city_id+'&'+city+'&'+country,
                #     "city_id": line['city_id'],
                #     "source_id": line['sid']
                # }

                #hilton
                args = {
                    'city_id': '',
                    'country_id': '',
                    'suggest': line['suggest'],
                    'source': line['source'],
                    'content': line['sid']
                }

                it.insert_task(args)
    city2list()
