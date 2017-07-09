#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/7 下午4:17
# @Author  : Hou Rong
# @Site    : 
# @File    : full_website_spider_task.py
# @Software: PyCharm
# coding=utf-8
import pymongo
import datetime
from .celery import app
from .my_lib.BaseTask import BaseTask
from my_lib.Common.Browser import MySession
from my_lib.full_website_parser.full_website_parser import full_website_parser
from my_lib.Common.RedisUrlSaver import UrlSaver

urlSaver = UrlSaver()

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['FullSiteSpider']['Attr']


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def full_site_spider(self, url, level, parent_url, parent_info, **kwargs):
    with MySession() as session:
        try:
            page = session.get(url)
            if 'text/html' in page.headers['Content-type']:
                # 解析
                img_url_set, pdf_url_set, next_url_set = full_website_parser(page.text, url)

                # 保存已抓取页面 url
                urlSaver.add_url(parent_url, url)

                # 保存结果信息
                collections.save({
                    'parent_url': parent_url,
                    'parent_info': parent_info,
                    'level': level,
                    'url': url,
                    'img_url': img_url_set,
                    'pdf_url': pdf_url_set,
                    'next_url': next_url_set,
                    'insert_time': datetime.datetime.now()
                })

                # 分发新的任务
                for next_url in next_url_set:
                    if not urlSaver.has_crawled(parent_url, next_url):
                        if level >= 0:
                            full_site_spider.delay(next_url, level - 1, parent_url, parent_info, **kwargs)

        except Exception as exc:
            session.update_proxy('23')
            self.retry(exc=exc)
