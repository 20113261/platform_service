#!/usr/bin/env python
# -*- coding:utf-8 -*-
from mioji import spider_factory
import json
from mioji.common.task_info import Task
from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.mysql_pool import service_platform_pool
from proj.my_lib.logger import func_time_logger
from mioji.spider_factory import factory
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Browser import proxy_pool
from celery.utils.log import get_task_logger
import mioji.common.logger
import mioji.common.pool
import mioji.common.pages_store
from lxml import html
import re
import time
from proj.my_lib.Common.Task import Task as Task_to
import requests
import traceback
mioji.common.pool.pool.set_size(1024)

logger = get_task_logger('daodaoHotel')
mioji.common.logger.logger = logger
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type
# 初始化工作 （程序启动时执行一次即可）
insert_db = None
# get_proxy = simple_get_socks_proxy
get_proxy = proxy_pool.get_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)


def hotel_url_to_database(source, keyword, need_cache=False):
    task = Task()
    task.ticket_info['url'] = keyword
    task.ticket_info['hotel_name'] = keyword
    old_target = source + 'ListHotel'
    spider = factory.get_spider_by_old_source(old_target)
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['hotel'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['hotel'], cache_config=none_cache_config)
    print(error_code)
    # if data_from == 'google':
    #     return error_code,spider.result,spider.user_datas['search_result']
    # print spider.result['hotel']
    return error_code, spider.result['hotel']


class OthersSourceHotelUrl(BaseSDK):

    def get_task_finished_code(self):
        return [0, 106, 107, 109, 29]

    def _execute(self, **kwargs):
        url = kwargs.get('url')
        tag = kwargs.get('tag')
        source = kwargs.get('source')
        name = kwargs.get('name')
        name_en = kwargs.get('name_en')
        city_id = kwargs.get('city_id')
        country_id = kwargs.get('country_id')
        table_name = 'list_result_{0}_{1}'.format(source, tag)

        t1 = time.time()
        error_code, hotel_result = hotel_url_to_database(
            source=source,
            keyword=url,
            need_cache=self.task.used_times == 0,
        )
        t2 = time.time()
        self.logger.info('抓取耗时：   {}'.format(t2 - t1))
        temp_save = []

        if source == 'daodao':
            for hotel in hotel_result:
                name = hotel.get('hotel_name', '')
                name_en = hotel.get('hotel_name_en', '')
                hotels = hotel.copy()
                status = 1 if hotels else 0
                temp_save.append((name, name_en, city_id, country_id, 'daodao', status, json.dumps(hotels) if hotels else None))

        elif source == 'google':
            for hotel in hotel_result:
                status = 1 if hotel_result else 0
                temp_save.append((name, name_en, city_id, country_id, 'google', status, json.dumps(hotel) if hotel else None))

        print temp_save
        @func_time_logger
        def hotel_list_insert_db(table_name, res_data):
            try:
                service_platform_conn = service_platform_pool.connection()
                cursor = service_platform_conn.cursor()
                sql = "replace into {} (name, name_en, city_id, country_id, `from`, status, source_list) VALUES (%s,%s,%s,%s,%s,%s,%s)".format(table_name)
                cursor.executemany(sql, res_data)
                service_platform_conn.commit()
                cursor.close()
                service_platform_conn.close()
            except Exception as e:
                self.logger.exception(msg="[mysql error]", exc_info=e)
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        hotel_list_insert_db(table_name, temp_save)
        t3 = time.time()
        self.logger.info('入库耗时：   {}'.format(t3 - t2))

        if len(temp_save) > 0:
            self.task.error_code = 0
        elif int(error_code) == 0:
            self.task.error_code = 29
            raise ServiceStandardError(ServiceStandardError.EMPTY_TICKET)
        else:
            raise ServiceStandardError(error_code=error_code)
        return len(temp_save), error_code

class ConversionDaodaoURL(BaseSDK):
    def _execute(self, **kwargs):
        id = kwargs['id']
        source = kwargs['source']
        url = kwargs['url']
        table_name = kwargs['table_name']
        t1 = time.time()
        url = url.replace('.cn', '.com')

        with MySession(need_cache=False, need_proxies=True) as session:
            resp = session.get(url)
            content = resp.text
            # print content
            real_url = None
            print id, source, url
            if source == 'agoda':
                agoda_json = re.search(r'window.searchBoxReact = (.*)(?=;)', content).group(1)
                agoda_json = json.loads(agoda_json)
                url = agoda_json.get('recentSearches', [])[0].get('data', {}).get('url')
                base_url = 'https://www.agoda.com/zh-cn'
                real_url = ''.join([base_url, url])
            elif source == 'booking':
                base_url = 'https://www.booking.com'
                root = html.fromstring(content)
                real_url = root.xpath('//div[@id="hotellist_inner"]//a')[0]
                real_url = ''.join([base_url, real_url.attrib.get('href').replace('-cn', '-com')])
            elif source == 'ctrip':
                ctrip_json = re.search(r'hotelPositionJSON: (.*)(?=,)', content).group(1)
                ctrip_json = json.loads(ctrip_json)
                url = ctrip_json[0].get('url')
                base_url = "http://hotels.ctrip.com"
                real_url = ''.join([base_url, url])
            elif source == 'elong':
                hotel_id = re.search(r'hotelId":"([0-9]+)"', content).group(1)
                real_url = 'http://ihotel.elong.com/{0}/'.format(hotel_id)
            elif source == 'expedia':
                raise Exception('我是expedia')
            elif source == 'hotels':
                root = html.fromstring(content)
                hotel_id = root.xpath('//div[@id="listings"]//li')[0].attrib.get('data-hotel-id')
                real_url = "https://ssl.hotels.cn/ho{0}/?pa=1&q-check-out=2018-04-16&tab=description&q-room-0-adults=2&YGF=7&q-check-in=2018-04-15&MGT=1&WOE=1&WOD=7&ZSX=0&SYE=3&q-room-0-children=0".format(
                    hotel_id)

        print real_url
        t2 = time.time()
        self.logger.info('抓取耗时：   {}'.format(t2 - t1))

        service_platform_conn = service_platform_pool.connection()
        cursor = service_platform_conn.cursor()
        sql = "update {0} set source_list = JSON_REPLACE(source_list, '$.hotels.{1}', %s) where id = %s".format(table_name, source);
        cursor.execute(sql, (real_url, id))
        service_platform_conn.commit()
        cursor.close()
        service_platform_conn.close()

        t3 = time.time()
        self.logger.info('入库耗时：   {}'.format(t3 - t2))

        self.task.error_code = 0
        return id, source, self.task.error_code




if __name__ == "__main__":
    # from proj.my_lib.Common.Task import Task as Task_to
    # url = "https://www.tripadvisor.cn/Hotels-g293938-Bandar_Seri_Begawan_Brunei_Muara_District-Hotels.html"
    # args = {
    #     'url': url,
    #     'source': 'daodao',
    #     'tag': '20180401a',
    #     'name': 'test_chinese',
    #     'name_en': 'test_english',
    # }
    # url = "格拉波斯克拉科夫公寓式酒店Aparthotel Globus Kraków"
    # args = {
    #     'url': url,
    #     'source': 'google',
    #     'tag': '20180401a',
    #     'name': '格拉波斯克拉科夫公寓式酒店',
    #     'name_en': 'Aparthotel Globus Kraków',
    #     'country': '218',
    #     'city': '10109',
    # }
    # task = Task_to(_worker='', _task_id='demo', _source='daodao', _type='suggest', _task_name='tes',
    #            _used_times=0, max_retry_times=6,
    #            kwargs=args, _queue='supplement_field',
    #            _routine_key='supplement_field', list_task_token='test', task_type=0, collection='')
    # ihg = OthersSourceHotelUrl(task)
    # ihg.execute()

    args = {
        'id': 5703,
        'source': 'hotels',
        'url': 'https://www.tripadvisor.cn/Commerce?p=HotelsCom2&src=69175783&geo=7940674&from=HotelDateSearch_Hotels&slot=3&matchID=1&oos=0&cnt=3&silo=6046&bucket=798156&nrank=3&crank=3&clt=D&ttype=DesktopMeta&tm=103267287&managed=false&capped=false&gosox=cgAmL4qe3gHkKQnzi9UKTVcHuZh0CwbiMUMVAh8NNB2poBnVsSGND7oFLmy_U-e3jSsfLxoZEtX3cqtoFCQVpLuwfbLhPBiXe9q736bRjuwsrWAnQzjurz7iIZpT-sIi3hsQXOC12mDIsgioZ3XGqt5ahLFHHUZrOU_t5ic8hQo&hac=AVAILABLE&mbl=LOSE&mbldelta=6641&rate=1255.51&fees=222.22&cur=RMB&adults=2&child_rm_ages=&inDay=22&outDay=23&rooms=1&inMonth=4&inYear=2018&outMonth=4&outYear=2018&auid=e6412165-3adc-4da1-b24f-86d08e4a8c5c&def_d=true&cs=1ddb974d6b5b29fe43d815bd46fa713ba&area=QC_Meta|Text|Available|Main|Desktop&tp=Hotels_ABList&ob=new_tab&ik=dfa16f9f16254037904013eddc4b2ed8&priceShown=1478&aok=1babeaa3b5b04b1981414fb169a8aa27',
        'table_name': 'list_aaaaa_daodao_20180401a',
    }

    task = Task_to(_worker='', _task_id='demo', _source='daodao', _type='suggest', _task_name='tes',
               _used_times=0, max_retry_times=6,
               kwargs=args, _queue='supplement_field',
               _routine_key='supplement_field', list_task_token='test', task_type=0, collection='')
    conversion = ConversionDaodaoURL(task)
    conversion.execute()