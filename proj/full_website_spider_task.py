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
MAX_LEVEL = 5

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['FullSiteSpider']['Attr']


@app.task(bind=True, max_retries=3, rate_limit='6/s')
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
                    'img_url': list(img_url_set),
                    'pdf_url': list(pdf_url_set),
                    'next_url': list(next_url_set),
                    'insert_time': datetime.datetime.now()
                })

                # 分发新的任务
                for next_url in next_url_set:
                    if not (
                                urlSaver.has_crawled(parent_url, next_url) or urlSaver.has_crawled('static_data',
                                                                                                   next_url)
                    ):
                        if level < MAX_LEVEL - 1:
                            # full_site_spider.delay(next_url, level + 1, parent_url, parent_info, **kwargs)
                            app.send_task('proj.full_website_spider_task.full_site_spider',
                                          args=(next_url, level + 1, parent_url, parent_info,),
                                          kwargs=kwargs,
                                          queue='full_site_task',
                                          routing_key='full_site_task')

            else:
                # 将非 html 页面入 set 防止多次抓取，保存已抓取页面 url
                urlSaver.add_url('static_data', url)

        except Exception as exc:
            session.update_proxy('23')
            self.retry(exc=exc)
