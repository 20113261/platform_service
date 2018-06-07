# -*- coding: UTF-8 -*-

'''
Created on 2016年12月1日

@author: dujun
'''
import tornado.web
from tornado.web import HTTPError
import json, os, traceback
from concurrent.futures import ThreadPoolExecutor
from mioji.dao import hotel_suggest_city_dao
from mioji.models.city_models import city_dic
from mioji.dao import file_dao

g_executor = ThreadPoolExecutor(32)

tr_f = '<tr>{0}</tr>'
td_f = '  <td>{0}</td>'


def td_line(row):
    if row:
        return tr_f.format('\n'.join([td_f.format(r) for r in row]))
    else:
        return ''


def city_str(row):
    return '</br>'.join(row)


class Handler(tornado.web.RequestHandler):
    executor = g_executor

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        yield self.async()

    @tornado.concurrent.run_on_executor
    def async(self):
        source = self.get_argument('source', None)
        label = int(self.get_argument('label', None))
        page = int(self.get_argument('page', '1'))

        lines = []
        lines.append(td_line(('city_id', 'city', 'suggests', 'select', 'label', 'error')))

        sug_list = hotel_suggest_city_dao.find_suggests(source, page, annotation=label)

        info_line = 'all:{}</br>'.format(len(sug_list))

        for sug in sug_list:
            r = (sug[1], city_str(city_dic.get(sug[1], '')), sug[3], sug[4], sug[5])
            lines.append(td_line(r))

        self.write(info_line + '<table border="1">\n' + '\n'.join(lines) + '</table>')


class AdminFileHandler(tornado.web.RequestHandler):
    executor = g_executor

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        name = self.get_argument('name', None)
        path = self.get_argument('path', None)

        file_path = file_dao.cache_dir
        if path:
            file_path += ('/' + path)

        file_path += ('/' + name)

        if not name or not os.path.exists(file_path):
            raise HTTPError(404)

        yield self.async(file_path, name)

    @tornado.concurrent.run_on_executor
    def async(self, file_path, name):
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % name)
        with open(file_path, "rb") as f:
            try:
                while True:
                    _buffer = f.read(4096)
                    if _buffer:
                        self.write(_buffer)
                    else:
                        f.close()
                        self.finish()
                        return
            except:
                raise HTTPError(404)
        raise HTTPError(500)
