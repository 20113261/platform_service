#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/7 下午4:17
# @Author  : Hou Rong
# @Site    : 
# @File    : full_website_spider_task.py
# @Software: PyCharm
# coding=utf-8
import pymongo
import pymongo.errors
import datetime
from .celery import app
from .my_lib.BaseTask import BaseTask
from my_lib.Common.Browser import MySession
from my_lib.full_website_parser.full_website_parser import full_website_parser
from my_lib.Common.RedisUrlSaver import UrlSaver

urlSaver = UrlSaver()
MAX_LEVEL = 3

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['FullSiteSpider']['HotelFullSite']


def save_crawl_result(parent_url, parent_info, level, url, **kwargs):
    try:
        collections.save({
            'parent_url': parent_url,
            'parent_info': parent_info,
            'level': level,
            'url': url,
            'img_url': kwargs.get('img_url', []),
            'pdf_url': kwargs.get('pdf_url', []),
            'unknown_static_file': kwargs.get('unknown_static_file', []),
            'next_url': kwargs.get('next_url', []),
            'insert_time': datetime.datetime.now()
        })
    except pymongo.errors.DuplicateKeyError as exc:
        print str(exc)


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='16/s')
def full_site_spider(self, url, level, parent_url, parent_info, **kwargs):
    self.task_source = 'TripAdvisor'
    self.task_type = 'WholeSiteCrawl'
    with MySession() as session:
        try:
            page = session.get(url)
            if ('text/html' in page.headers['Content-type']) or ('text/plain' in page.headers['Content-type']):
                # 解析
                img_url_set, pdf_url_set, next_url_set = full_website_parser(page.text, url)

                # 保存已抓取页面 url
                urlSaver.add_url(parent_url, url)

                # 保存结果信息
                save_crawl_result(parent_url, parent_info, level, url, img_url=list(img_url_set),
                                  pdf_url=list(pdf_url_set), next_url=list(next_url_set))

                # 分发新的任务
                for next_url in next_url_set:
                    if not (
                                    urlSaver.has_crawled(parent_url, next_url) or
                                    urlSaver.has_crawled('static_data', next_url) or
                                urlSaver.crawled_enough(parent_url)
                    ):
                        if level < MAX_LEVEL - 1:
                            # 发任务的时候就添加已抓取 url，防止因中间的时间间隔导致队列中任务指数暴增
                            urlSaver.add_url(parent_url, next_url)

                            # full_site_spider.delay(next_url, level + 1, parent_url, parent_info, **kwargs)
                            app.send_task('proj.full_website_spider_task.full_site_spider',
                                          args=(next_url, level + 1, parent_url, parent_info,),
                                          kwargs=kwargs,
                                          queue='full_site_task',
                                          routing_key='full_site_task')
            elif 'image' in page.headers['Content-type']:
                # 无法直接从页面信息中查看到是否为图片的页面，通过 Content-type 检测是否为图片，并入库保存
                urlSaver.add_url(parent_url, url)
                save_crawl_result(parent_url, parent_info, level, url, img_url=[url, ])

            elif 'application/pdf' in page.headers['Content-type']:
                # 无法直接从页面信息中查看到是否为 pdf 的页面，通过 Content-type 检测是否为 pdf，并入库保存
                urlSaver.add_url(parent_url, url)
                save_crawl_result(parent_url, parent_info, level, url, pdf_url=[url, ])
            else:
                # 将非 html 页面入 set 防止多次抓取，保存已抓取页面 url , 文件类型诸如 mp3 rar 等格式
                urlSaver.add_url('static_data', url)
                save_crawl_result(parent_url, parent_info, level, url, unknown_static_file=[url, ])

        except Exception as exc:
            session.update_proxy('23')
            self.retry(exc=exc)
