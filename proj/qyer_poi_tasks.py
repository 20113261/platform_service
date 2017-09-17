# coding=utf-8
import time
import traceback

import requests
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from proj.my_lib.PageSaver import save_task_and_page_content
from proj.celery import app
from proj.my_lib.my_qyer_parser.data_obj import DBSession
from proj.my_lib.my_qyer_parser.my_parser import page_parser
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.Common.Browser import MySession


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='6/s')
def qyer_poi_task(self, target_url, city_id, **kwargs):
    self.task_source = 'Qyer'
    self.task_type = 'Qyerinfo'

    with MySession() as session:
        page = session.get(target_url, timeout=240)
        page.encoding = 'utf8'
        content = page.text
        save_task_and_page_content(task_name='qyer_poi', content=content, task_id=kwargs['mongo_task_id'], source='qyer',
                                   source_id='NULL',
                                   city_id='NULL', url=target_url)
        result = page_parser(content=content, target_url=target_url)
        result.city_id = city_id
        if result.name == 'NULL' and result.map_info == 'NULL':
            raise Exception('name or map_info is NULL')
        else:
            session = DBSession()
            session.merge(result)
            session.commit()
            session.close()

        self.error_code = 0
        return result
