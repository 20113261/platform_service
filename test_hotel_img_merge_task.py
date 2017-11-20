#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/8 上午8:19
# @Author  : Hou Rong
# @Site    :
# @File    : mongo_task.py
# @Software: PyCharm
from data_source import MysqlSource
from proj.my_lib.logger import get_logger
from MongoTaskInsert import InsertTask

logger = get_logger("insert_mongo_task")

spider_data_base_data_config = {
    'host': '10.10.228.253',
    'user': 'mioji_admin',
    'password': 'mioji1109',
    'charset': 'utf8',
    'db': 'base_data'
}


def get_tasks():
    query_sql = '''SELECT uid
FROM hotel
ORDER BY uid;'''

    for _l in MysqlSource(db_config=spider_data_base_data_config,
                          table_or_query=query_sql,
                          size=10000, is_table=False,
                          is_dict_cursor=False):
        yield _l[0]


if __name__ == '__main__':
    with InsertTask(worker='proj.total_tasks.hotel_img_merge_task', queue='merge_task', routine_key='merge_task',
                    task_name='merge_hotel_image_20171116_40', source='Any', _type='HotelImgDownloader',
                    priority=11) as it:
        _count = 9
        for uid in get_tasks():
            _count += 1
            args = {
                'uid': uid,
                'min_pixels': '400000',
                'target_table': 'hotel_40'
            }
            it._insert_task(args)
            if _count % 10000 == 0:
                break
