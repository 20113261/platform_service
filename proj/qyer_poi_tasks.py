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
from proj.my_lib.new_hotel_parser.data_obj import text_2_sql
from sqlalchemy.sql import text


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='6/s')
def qyer_poi_task(self, target_url, city_id, **kwargs):
    self.task_source = 'Qyer'
    self.task_type = 'Qyerinfo'

    with MySession(need_cache=True) as session:
        page = session.get(target_url, timeout=240)
        page.encoding = 'utf8'
        content = page.text
        result = page_parser(content=content, target_url=target_url)
        result.city_id = city_id
        if result.name == 'NULL' and result.name_en == 'NULL':
            self.error_code = 102
            raise Exception("name and name_en all NULL")
        elif result.map_info == 'NULL':
            self.error_code = 102
            raise Exception('map_info is NULL')
        else:

            sql_result = result.__dict__
            sql_key = sql_result.keys()
            if '_sa_instance_state' in sql_key:
                sql_key.remove('_sa_instance_state')

            try:
                session = DBSession()
                # session.merge(result)
                session.execute(text(text_2_sql(sql_key).format(table_name=kwargs['task_name'])), [sql_result])
                session.commit()
                session.close()
            except Exception as e:
                self.error_code = 33
                raise e

        self.error_code = 0
        return self.error_code
