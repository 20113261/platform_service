#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/20 上午10:20
# @Author  : Hou Rong
# @Site    : 
# @File    : spider_init_new.py
# @Software: PyCharm

# coding=utf-8
# coding='utf8'
import re

from proj.celery import app
from proj.tasks import get_comment


def add_target(task_url, miaoji_id, **kwargs):
    res1 = get_comment.delay(task_url, 'zhCN', miaoji_id, **kwargs)
    res2 = get_comment.delay(task_url, 'en', miaoji_id, **kwargs)
    return res1, res2


d_pattern = re.compile('-d(\d+)')

if __name__ == '__main__':
    # from proj.hotel_static_tasks import hotel_static_base_data
    #
    # print hotel_static_base_data('7ededbc01f00e0463f064e6ca9f8235f', 'hotel_base_data_170612')

    # from proj.suggestion_task import ctrip_suggestion_task

    # ctrip_suggestion_task.delay('10001', '巴黎', task_id='test')
    # ctrip_suggestion_task("10025", "sk\u00e4rholmen")

    # kwargs = {}
    # app.send_task('proj.full_website_spider_task.full_site_spider',
    #               args=('http://www.parcjeandrapeau.com', 0, 'http://www.parcjeandrapeau.com', {'id': 'v514490'},),
    #               kwargs=kwargs,
    #               queue='hotel_task',
    #               routing_key='hotel_task')

    # todo Trip Advisor List
    # import dataset
    # import re
    # from proj.tripadvisor_list_tasks import init_header
    #
    # db = dataset.connect('mysql+pymysql://hourong:hourong@10.10.180.145/SuggestName?charset=utf8')
    #
    # _count = 0
    # for line in db['DaodaoSuggestCityUrl']:
    #     _count += 1
    #     city_id = line['city_id']
    #     if city_id == '10001':
    #         continue
    #
    #     try:
    #         source_city_id = re.findall('-g(\d+)', line['daodao_url'])[-1]
    #     except Exception:
    #         continue
    #     # print city_id, source_city_id
    #     if _count % 1000 == 0:
    #         print _count
    #
    #     ctx = init_header(source_city_id, 0)
    #     t_id = app.send_task('proj.tripadvisor_list_tasks.list_page_task',
    #                          args=(ctx, city_id,),
    #                          kwargs={'task_id': 'test'},
    #                          queue='tripadvisor_list_tasks',
    #                          routing_key='tripadvisor_list_tasks')
    #     print t_id
    # print _count

    '''
    File Downloader Task
    '''

    # from proj.file_downloader_task import file_downloader
    #
    # # print file_downloader('https://ccm.ddcdn.com/ext/photo-s/01/bd/57/a2/kilauea-caldera.jpg', 'img', '/tmp/ab/c/d/', )
    # t_id = app.send_task('proj.file_downloader_task.file_downloader',
    #                      args=('https://ccm.ddcdn.com/ext/photo-s/01/bd/57/a2/kilauea-caldera.jpg', 'img',
    #                            '/tmp/ab/c/d/',),
    #                      kwargs={'task_id': 'test'},
    #                      queue='file_downloader',
    #                      routing_key='file_downloader')
    # print t_id
    # import proj.tripadvisor_website_task
    #
    # proj.tripadvisor_website_task.website_url_task('233464',
    #                                                'http://www.tripadvisor.cn/ShowUrl?&excludeFromVS=false&odc=BusinessListingsUrl&d=233464&url=0')

    import pymysql
    import pymongo

    client = pymongo.MongoClient(host='10.10.231.105')
    collections = client['TripAdvisor']['website']

    sid_set = set()
    for line in collections.find():
        sid_set.add(line['source_id'])

    conn = pymysql.connect(host='10.10.228.253', user='mioji_admin', password='mioji1109', db='hotel_adding',
                           charset='utf8')
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT
             source_id,
             description
FROM hotelinfo_tripadvisor_0717_bak
WHERE description != 'NULL' AND description != '';''')
    for line in cursor.fetchall():
        source_id, website_url = line
        if source_id not in sid_set:
            # print source_id, website_url
            t_id = app.send_task('proj.tripadvisor_website_task.website_url_task',
                                 args=(source_id,
                                       website_url,),
                                 kwargs={},
                                 queue='tripadvisor_website',
                                 routing_key='tripadvisor_website')
            print t_id
