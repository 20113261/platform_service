#!/usr/bin/env python
# -*- coding:utf-8 -*-

from sqlalchemy.sql import text

from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.KeyMatch import key_is_legal
from proj.my_lib.Common.NetworkUtils import google_get_map_info
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.ServiceStandardError import TypeCheckError
from proj.my_lib.logger import get_logger
from proj.my_lib.my_qyer_parser.data_obj import DBSession
from proj.my_lib.my_qyer_parser.my_parser import page_parser
from proj.my_lib.new_hotel_parser.data_obj import text_2_sql
from proj.my_lib.Common.Utils import retry
from lxml import html
import json
import pymongo
from urlparse import urljoin

mongo_config = {
    'host': '10.10.213.148'
}
logger = get_logger("QyerPoiCity")

search_url = 'https://www.baidu.com/s'

headers = {
    'Host': 'www.baidu.com',
    'is_referer': 'https://www.baidu.com/',
    'is_xhr': '1',
    'Referer': 'https://www.baidu.com/',
}


class BaiDuSearchSDK(BaseSDK):
    @retry(times=5)
    def _execute(self, **kwargs):
        with MySession(need_cache=True, need_proxies=True) as session:
            keyword = self.task.kwargs['keyword']
            page_info = {}
            response = session.get(
                url=search_url,
                params={
                    'ie': 'utf-8',
                    'tn': 'baidu',
                    'wd': keyword,
                    'rqlang': 'cn'
                },
                headers=headers
            )
            try:
                content = response.content
                root = html.fromstring(content)
                page_info['keyword'] = keyword
                page_info['content'] = content
                city_url = []
                city_list = root.xpath('//a[contains(text(),"place.qyer.com")]/text()')
                for city in city_list:
                    url_str = urljoin('http:', city)
                    url_str = url_str.strip('.').strip('')
                    if not city_url or url_str not in city_url:
                        city_url.append(url_str)
                page_info['city_url'] = city_url
                client = pymongo.MongoClient(**mongo_config)
                db = client['SuggestName']
                db.BaiDuSuggest.save(page_info)
            except Exception as e:
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)
        self.task.error_code = 0
        return page_info
