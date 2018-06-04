#coding:utf-8
# @Time    : 2018/5/24
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : query_server.py
# @Software: PyCharm
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.concurrent
import json
# import memory_profiler
import os
import math
import redis
import datetime
import pymongo
import pyrabbit
import torndb
from tornado.options import define, options
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from rabbitmq_func import detect_msg_num
from my_logger import get_logger
from proj import mysql_pool


log = get_logger('web_interface_server')

client = pymongo.MongoClient(host='mongodb://root:miaoji1109-=@10.19.2.103:27017/')
db = client['MongoTask_Zxp']

class Executor(ThreadPoolExecutor):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not getattr(cls, '_instance', None):
            cls._instance = ThreadPoolExecutor(max_workers=args[0])
        return cls._instance


class QueryTask(tornado.web.RequestHandler):
    executor = Executor(5)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        try:
            task_name = self.get_argument('task_name', '')
            code = int(self.get_argument('code', '')) if self.get_argument('code', '') != '' else ''
            count = int(self.get_argument('count', '')) if self.get_argument('count', '') != '' else ''
            database = self.get_argument('database', '')
            print('来了')
            if task_name != '' and code != '' and count != '':
                yield self.async_get_code(task_name, code, count)
            elif task_name != '' and database == 'test':
                yield self.async_get_statisic(task_name)
            elif task_name != '' and database == 'task':
                yield self.async_get_code_distribute(task_name)
        except Exception as e:
            print('出错了')

    @tornado.concurrent.run_on_executor
    def async_get_statisic(self, task_name):
        # idle_seconds, message_count, max_message_count = detect_msg_num(queue_name)
        r = redis.Redis(host='10.10.180.145', db=15)
        res = r.zrange(task_name, 0, -1, withscores=True)
        self.write(str(res))

    @tornado.concurrent.run_on_executor
    def async_get_code(self, task_name, code, count):
        colls = db.collection_names()
        for coll in colls:
            if task_name in coll:
                res = db[coll].find({'error_code': code}).limit(count)
        content = ''
        num = 0
        for i in res:
            num += 1
            content = content + str(num) + '、 '
            content += str(i)
            content += '<br><br>'
        self.write(content)

    @tornado.concurrent.run_on_executor
    def async_get_code_distribute(self, task_name):
        colls = db.collection_names()
        for coll in colls:
            if task_name in coll:
                res = db[coll].aggregate([{'$group':{'_id':'$error_code','counter':{'$sum':1}}}])
        content = ''
        for i in res:
            content += str(i)
            content += '<br><br>'
        self.write(content)


class MqTask(tornado.web.RequestHandler):
    executor = Executor(5)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        task_name = self.get_argument('task_name', '')
        update = self.get_argument('update', '')
        if task_name and update:
            queue = '_'.join(task_name.split('_')[-4:-1])

            yield self.delete_queue(queue)
            if update == 'stop':
                yield self.update_mysql(task_name, 1)
            elif update == 'restart':
                yield self.update_mysql(task_name, 0)

    @tornado.concurrent.run_on_executor
    def delete_queue(self, queue, **kwargs):
        try:
            zxp = pyrabbit.Client('47.93.188.221:12345', 'zxp', 'zxp')
            zxp.delete_queue('serviceplatform', queue)
        except Exception as e:
            self.write('刪除任务队列失败，请检查是否存在该队列')

            log.info('刪除任务队列失败，请检查是否存在该队列')

    def update_mysql(self, task_name, finished):
        try:
            self.db = torndb.Connection(
                host="10.10.238.148",
                database="task_db",
                user="mioji_admin",
                password="mioji1109"
            )
            # res = self.db.execute("select * from task_serviceplatform_monitor where collection_name like %s", str('%'+task_name))
            self.db.execute("update task_serviceplatform_monitor set finished=%s where collection_name like %s", finished, str('%'+task_name))
        except Exception as e:
            self.write('停止任务分发失败，请检查！')
        finally:
            self.db.close()


class Application(tornado.web.Application):
    def __init__(self, handlers, **settings):

        super(Application, self).__init__(handlers, **settings)



application = Application([
    (r'/query', QueryTask),
    (r'/mq', MqTask),
])


print()

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.bind(port=12346)
    http_server.start()
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()
