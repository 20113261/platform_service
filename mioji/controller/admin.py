#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月24日

@author: dujun
'''

from mioji import spider_factory


def spider_status():
    return spider_factory.factory.all()


def reload():
    return spider_factory.factory.reload()


# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月1日

@author: dujun
'''
import tornado.web
import json
import traceback
from author_utils import admin_authenticated
from mioji.common.logger import logger
from utils import executor
from mioji import spider_factory

from json import JSONEncoder
import inspect


class MyEncoder(JSONEncoder):
    def default(self, o):
        file_name = inspect.getfile(o)
        cls_name = o.__name__
        return '{0} : {1}'.format(file_name, cls_name)


def status(handler):
    '''
    status
    '''
    return '<pre>{0}</pre>'.format(json.dumps(spider_factory.factory.all(), indent=2, cls=MyEncoder, sort_keys=True))


def reloadSpider(handler):
    '''
    更新爬虫
    '''
    return '<pre>{0}</pre>'.format(json.dumps(spider_factory.factory.reload(), indent=2, cls=MyEncoder, sort_keys=True))


binds = {'status': status,
         'reload': reloadSpider,
         }

api_doc = None
api_doc_list = []
for api, func in binds.iteritems():
    doc = '<b>' + api + '</b>' + func.__doc__ + '\n\n'
    api_doc_list.append(doc)
api_doc = '<pre><b>supported admin api</b>\n\n' + ''.join(api_doc_list) + '</pre>'


class AdminHandler(tornado.web.RequestHandler):
    executor = executor

    @admin_authenticated
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        logger.info(str(self.request))
        option = self.get_argument('option', None)
        if not option or not binds.get(option, None):
            self.write(api_doc)
        else:
            yield self.async_do(option)

    @tornado.concurrent.run_on_executor
    def async_do(self, option):
        try:
            func = binds.get(option, None)
            r = func(self)
            self.write(r)
        except Exception, e:
            self.write('request error{0}\n{1}'.format(traceback.format_exc(), api_doc))


if __name__ == '__main__':
    print status(None)
