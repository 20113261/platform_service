#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年3月1日

@author: dujun
'''
import tornado.web
import json
import traceback, logging
from mioji.common.logger import logger
from mioji.common.task_info import Task
from utils import executor
from mioji import spider_factory
from mioji.common.utils import simple_get_proxy
from mioji.common.pages_store import cache_dir

get_proxy = simple_get_proxy
# get_proxy = None
spider_factory.config_spider(None, get_proxy, False)
cache_dir = '/search/spider_cache'

logger.setLevel(logging.DEBUG)


class SpiderHandler(tornado.web.RequestHandler):
    executor = executor

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        try:
            source = self.get_argument('source', None)
            source_type = self.get_argument('source_type', None)
            task = self.get_argument('task', {})
            logger.info('task_info={0}'.format(task))
            print task

            if source and source_type and task:
                spider = spider_factory.factory.get_spider(source, source_type)
                info = json.loads(task)
                spider.debug = True
                spider.task = Task(source, info.get('content', None), info.get('extra', {}))
                for k, v in info.iteritems():
                    if k not in ['content', 'extra']:
                        spider.task.__setattr__(k, v)

                yield self.async_do(spider)
        except:
            self.write('<pre>{0}</pre>'.format(traceback.format_exc()))

    @tornado.concurrent.run_on_executor
    def async_do(self, spider):
        try:
            code = spider.crawl()
            res = {
                'code': code,
                'result': spider.result
            }
            print res
            self.write(
                '<pre>{0}</pre> <br/><p>debug:</p><pre>{1}</pre>'.format(json.dumps(res, ensure_ascii=False, indent=2),
                                                                         spider.verify_data))
        except:
            self.write(
                '<pre>{0}</pre> <br/><p>debug:</p><pre>{1}</pre>'.format(traceback.format_exc(), spider.verify_data))
