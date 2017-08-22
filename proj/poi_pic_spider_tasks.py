#!/usr/bin/env python
# encoding:utf-8

import sys
import time
import traceback

from common.common import get_proxy, update_proxy

from proj.celery import app
from proj.my_lib.parse_view_pic.base_parse import GooglePicSpider, FlickrPicSpider, ShutterShockPicSpider
from proj.my_lib.parse_view_pic.mysql_ext import PicModel
from proj.my_lib.parse_view_pic.pic_data_assembly import flickr_pic_data_assembly
from proj.my_lib.parse_view_pic.pic_data_assembly import google_pic_data_assembly
from proj.my_lib.parse_view_pic.pic_data_assembly import shutter_pic_data_assembly
from proj.my_lib.parse_view_pic.poi_pic_config import save_db_config
from proj.my_lib.task_module.task_func import update_task
from proj.my_lib.BaseTask import BaseTask

reload(sys)
sys.setdefaultencoding("utf-8")


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def google_spider(self, vid, search_kw, debug=False, **kwargs):
    """
    Google 图片搜索爬取
    """
    if search_kw is None or search_kw == "null":
        # todo logging null key words
        return None
    x = time.time()
    spider_proxy = 'socks5://' + get_proxy(source="Platform")
    try:
        spider = GooglePicSpider(search_kw, spider_proxy, debug)
        pic_ret = spider.pic_search()
        pic_save_data = google_pic_data_assembly(vid, search_kw, pic_ret)
        spider_db = PicModel(**save_db_config)
        for _, save_data_map in pic_save_data.items():
            spider_db.insert_pic_many(save_data_map["table"],
                                      save_data_map["fields"],
                                      save_data_map["values"])
        update_task(kwargs['task_id'])
    except Exception as exc:
        update_proxy('Platform', spider_proxy, x, '23')
        self.retry(exc=traceback.format_exc(exc))


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def flickr_spider(self, vid, search_kw, debug=False, **kwargs):
    """
    flickr 图片搜索爬取
    """
    if search_kw is None or search_kw == "null":
        # todo logging null key words
        return None
    x = time.time()
    spider_proxy = 'socks5://' + get_proxy(source="Platform")
    try:
        spider = FlickrPicSpider(search_kw, spider_proxy, debug)
        pic_ret = spider.pic_search()
        pic_save_data = flickr_pic_data_assembly(vid, search_kw, pic_ret)
        spider_db = PicModel(**save_db_config)
        for _, save_data_map in pic_save_data.items():
            spider_db.insert_pic_many(save_data_map["table"],
                                      save_data_map["fields"],
                                      save_data_map["values"])
        update_task(kwargs['task_id'])
    except Exception as exc:
        update_proxy('Platform', spider_proxy, x, '23')
        self.retry(exc=traceback.format_exc(exc))


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def shutter_spider(self, vid, search_kw, debug=False, **kwargs):
    """
    shutterstock 图片搜索爬取
    """
    if search_kw is None or search_kw == "null":
        # todo logging null key words
        return None
    x = time.time()
    spider_proxy = 'socks5://' + get_proxy(source="Platform")
    try:
        spider = ShutterShockPicSpider(search_kw, spider_proxy, debug)
        pic_ret = spider.pic_search()
        pic_save_data = shutter_pic_data_assembly(vid, search_kw, pic_ret)
        spider_db = PicModel(**save_db_config)
        for _, save_data_map in pic_save_data.items():
            spider_db.insert_pic_many(save_data_map["table"],
                                      save_data_map["fields"],
                                      save_data_map["values"])
        update_task(kwargs['task_id'])
    except Exception as exc:
        update_proxy('Platform', spider_proxy, x, '23')
        self.retry(exc=traceback.format_exc(exc))
