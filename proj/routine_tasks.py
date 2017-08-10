#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/10 上午8:53
# @Author  : Hou Rong
# @Site    : 
# @File    : routine_tasks.py
# @Software: PyCharm
import proj.my_lib.parser_exception
from proj.my_lib.PageSaver import save_task_and_page_content
from proj.my_lib.shop_parser import parse as shop_parse, insert_db as shop_insert_db
from proj.celery import app
from proj.my_lib.BaseRoutineTask import BaseRoutineTask
from proj.my_lib.Common.Browser import MySession


@app.task(bind=True, base=BaseRoutineTask, max_retries=5, rate_limit='6/s')
def shop_routine(self, target_url, **kwargs):
    with MySession() as session:
        try:
            page = session.get(target_url)
            page.encoding = 'utf8'
        except Exception as exc:
            exc.error_code = proj.my_lib.parser_exception.PROXY_INVALID
            raise exc
        try:
            result = shop_parse(page.content, target_url)
        except Exception as exc:
            exc.error_code = proj.my_lib.parser_exception.PARSE_ERROR
            raise exc

        try:
            print shop_insert_db(result, 'NULL')
        except Exception as exc:
            exc.error_code = proj.my_lib.parser_exception.STORAGE_ERROR
            raise exc

        try:
            save_task_and_page_content(task_name='daodao_poi_shop', content=page.content,
                                       task_id=kwargs['mongo_task_id'],
                                       source='daodao',
                                       source_id='NULL',
                                       city_id='NULL', url=target_url)
        except Exception as exc:
            exc.error_code = 100
            raise exc


@app.task(bind=True, base=BaseRoutineTask, max_retries=5, rate_limit='6/s')
def test():
    e = Exception()
    e.error_code = 123
    raise e

if __name__ == '__main__':
    test()
