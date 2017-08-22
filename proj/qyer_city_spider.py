# coding=utf-8
import sys
import time
import traceback

from common.common import get_proxy, update_proxy
from lxml import etree

from proj.celery import app
from proj.my_lib.platform_qyer_city.conf.config import save_db_config
from proj.my_lib.platform_qyer_city.lib.mysql_ext import QyerModel
from proj.my_lib.platform_qyer_city.lib.qyer_http import init_qyer_session
from proj.my_lib.platform_qyer_city.lib.qyer_parse import find_max_page
from proj.my_lib.platform_qyer_city.lib.qyer_parse import platform_page_parse, city_state
from proj.my_lib.task_module.task_func import update_task
from proj.my_lib.BaseTask import BaseTask

reload(sys)
sys.setdefaultencoding("utf-8")


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def qyer_city_spider(self, country_id, country_en, country_link, debug=False, **kwargs):
    """
    抓取穷游上的城市数据
    country_id:
        int, index country info
    country_en:
        str. country_en
    country_link:
        str.
    """
    if country_en in city_state:
        country_type = "city_state"
    else:
        country_type = "city_list"
    http_tools = init_qyer_session(debug=True)
    x = time.time()
    country_args = {"country_en": country_en,
                    "country_id": country_id}
    spider_proxy = "socks5://" + get_proxy(source="Platform")
    qyer_db = QyerModel(**save_db_config)

    try:
        spider_ret = http_tools(country_link, proxy=spider_proxy)
        status_code = spider_ret[1]
        if status_code != 200 and status_code != 404:
            raise Exception(str(status_code))

        save_data = platform_page_parse(country_type,
                                        spider_ret[0],
                                        **country_args)
        qyer_db.insert_many_data(*save_data)
    except Exception as exc:
        update_proxy('Platform', spider_proxy, x, '23')
        self.retry(exc=traceback.format_exc(exc))


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def qyer_country_spider(self, country_id, country_link, debug=False, **kwargs):
    """
    抓取穷游上的城市数据
    country_id:
        int, index country info
    country_en:
        str. country_en
    country_link:
        str.
    """
    http_tools = init_qyer_session(debug=True)
    x = time.time()
    spider_proxy = "socks5://" + get_proxy(source="Platform")
    qyer_db = QyerModel(**save_db_config)

    try:
        spider_ret = http_tools(country_link, proxy=spider_proxy)
        status_code = spider_ret[1]
        if status_code != 200 and status_code != 404:
            raise Exception(str(status_code))

        page_html = etree.HTML(spider_ret[0])
        country_max_page = find_max_page(page_html)
        save_data = [country_max_page, country_id]
        qyer_db.update_country_page(save_data)
        update_task(kwargs['task_id'])
    except Exception as exc:
        update_proxy('Platform', spider_proxy, x, '23')
        self.retry(exc=traceback.format_exc(exc))
