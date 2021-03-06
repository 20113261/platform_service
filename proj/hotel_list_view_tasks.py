#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from __future__ import absolute_import
# import os
# os.environ["CONFIG_FILE"] = '/root/data/lib/slave_develop_new/workspace/spider/SpiderClient/conf/conf_lwn.ini'
# from celery.utils.log import get_task_logger
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from mioji import spider_factory
from mioji.common.utils import simple_get_socks_proxy
import mioji.common.spider
import mioji.common.logger
import datetime
import mioji.common.pool
import traceback
from sqlalchemy import Column, String, Text, create_engine, TIMESTAMP, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class HotelViewList(Base):
    __tablename__ = 'poi_attr_new'
    source = Column(String(64), primary_key=True)
    source_id = Column(Integer, primary_key=True)
    city_id = Column(Integer, primary_key=True)
    url = Column(Text, nullable=False)
    name = Column(String(512), nullable=False)
    utime = Column(DateTime, default=datetime.datetime.now)


from proj.my_lib.logger import get_logger

logger = get_logger("viewDaodao")

mioji.common.spider.NEED_FLIP_LIMIT = False
mioji.common.pool.pool.set_size(2024)

# from proj.test_spider import DaodaoViewSpider

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)
mioji.common.spider.NEED_FLIP_LIMIT = False

# logger = get_task_logger(__name__)
mioji.common.logger.logger = logger

# mysql connect pool
db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='base_data'
)

URL = 'https://www.tripadvisor.com.hk'

engine_mb4 = create_engine('mysql+pymysql://mioji_admin:mioji1109@10.10.228.253:3306/base_data?charset=utf8mb4',
                           encoding="utf-8", pool_size=100, pool_recycle=3600, echo=False)
DBSession_mb4 = sessionmaker(bind=engine_mb4)


def hotel_list_database(source, url):
    task = Task()
    task.content = URL + url
    task.source = source.lower().capitalize() + 'ListInfo'
    spider = factory.get_spider('daodao', task.source)
    # spider = factory.get_spider_by_old_source(task.source)
    # spider = DaodaoViewSpider()
    spider.task = task
    code = spider.crawl(required=['view'])
    return code, spider.result.get('view', {})


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='5/s')
def hotel_view_list_task(self, source, url, city_id, **kwargs):
    try:
        self.task_source = source.title()
        self.task_type = 'DaodaoListInfo'
        logger.info("任务进行中。。。")
        code, result = hotel_list_database(source, url)
        logger.info("code : %s" % str(code))

        if int(code) != 0:
            logger.info("=======================0=========================\n")
            logger.info(str(code) + '   |   ' + str(result))
            logger.info("\n=======================1=========================")
            raise Exception

        for one in result:
            for key, view in one.items():
                View = HotelViewList()
                View.source = source
                View.source_id = int(view['source_id'])
                View.city_id = int(city_id)
                View.url = view['view_url']
                View.name = view['view_name'].strip('\n').strip()

                try:
                    ss = DBSession_mb4()
                    ss.merge(View)
                    ss.commit()
                except Exception as e:
                    logger.info("======================= sql 异常=========================")
                    logger.exception(traceback.format_exc(e))

        return True
    except Exception as e:
        logger.exception('==================  异常  0==================')
        logger.exception(source + ' | ' + str(city_id) + ' | ' + url)
        logger.exception(traceback.format_exc(e))
        logger.exception('==================  异常  1==================')
        raise Exception(e)


if __name__ == '__main__':
    print hotel_view_list_task('daodao', '/Tourism-g4665321-Mendocino_County_California-Vacations.html', '29106')
