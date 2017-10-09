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
from proj.my_lib.logger import get_logger
from proj.my_lib.ServiceStandardError import TypeCheckError
from proj.my_lib.Common.KeyMatch import key_is_legal
from proj.my_lib.Common.NetworkUtils import google_get_map_info

logger = get_logger("QyerPoiDetail")


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='1/s')
def qyer_poi_task(self, target_url, city_id, **kwargs):
    task_response = kwargs['task_response']
    task_response.source = 'Qyer'
    task_response.type = 'Qyerinfo'

    with MySession(need_cache=True) as session:
        page = session.get(target_url, timeout=240)
        page.encoding = 'utf8'
        content = page.text
        result = page_parser(content=content, target_url=target_url)
        result.city_id = city_id

        retry_count = kwargs['retry_count']

        name = result.name
        name_en = result.name_en
        map_info = result.map_info
        address = result.address

        if not key_is_legal(map_info) or map_info == "0.000000,0.000000":
            if retry_count > 3:
                if not key_is_legal(address):
                    raise TypeCheckError(
                        'Error map_info and address NULL        with parser %ss    url %s' % (
                            page_parser.func_name, target_url))
                google_map_info = google_get_map_info(address)
                if not key_is_legal(google_map_info):
                    raise TypeCheckError(
                        'Error google_map_info  NULL        with parser %ss    url %s' % (
                            page_parser.func_name, target_url))
                result.map_info = google_map_info
            else:
                raise TypeCheckError(
                    'Error map_info NULL        with parser %ss    url %s' % (page_parser.func_name, target_url))

        if key_is_legal(name) or key_is_legal(name_en):
            logger.info(name + '  ----------  ' + name_en)
        else:
            raise TypeCheckError(
                'Error name and name_en Both NULL        with parser %s    url %s' % (
                    page_parser.func_name, target_url))

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
        task_response.error_code = 33
        raise e

    task_response.error_code = 0
    return task_response.error_code
