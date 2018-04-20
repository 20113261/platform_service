#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月16日

@author: dujun
'''
import gevent.monkey
gevent.monkey.patch_all()

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.concurrent
import tornado.gen
from concurrent.futures import ThreadPoolExecutor
from tornado.options import define, options
from mioji.common.pages_store import get_by_md5
from mioji.controller import city_label
from mioji.controller import admin, spider_debug

port = 18089
define("port", default=port, help="Run server on a specific port", type=int)
tornado.options.parse_command_line()
# executor_pool = ThreadPoolExecutor(1)
executor_pool = ThreadPoolExecutor(1)


class CachePage(tornado.web.RequestHandler):
    executor = executor_pool

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        md5 = self.get_argument('md5', '').strip()
        page = yield self.async_get(md5)
        self.write(page)
        return

    @tornado.concurrent.run_on_executor
    def async_get(self, md5):
        page = get_by_md5(md5)
        return page


application = tornado.web.Application([
    (r'/page', CachePage),
    (r'/suggests', city_label.Handler),
    (r'/admin', admin.AdminHandler),
    (r'/download', city_label.AdminFileHandler),
    (r'/spider', spider_debug.SpiderHandler),
])

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.bind(port, '0.0.0.0')
    http_server.start()
    tornado.ioloop.IOLoop.instance().start()
