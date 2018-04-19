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
import urlparse
from lxml import html
import re
import time
import pymongo
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
clients = pymongo.MongoClient(host='10.10.231.105')
SourceIDS = clients['ImagesMD5']['SourceId']


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
        source_id = kwargs.get('source_id')
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

        # print temp_save
        @func_time_logger
        def hotel_list_insert_daodao(table_name, res_data):
            try:
                service_platform_conn = service_platform_pool.connection()
                cursor = service_platform_conn.cursor()
                sel_sql = 'select id, localtion_id, source_list from {} where source_id = %s'.format(table_name)
                rep_sql = "replace into {} (id, name, name_en, city_id, country_id, `from`, source_id, localtion_id, status, source_list) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                    table_name)
                ins_sql = "insert into {} (name, name_en, city_id, country_id, `from`, source_id, localtion_id, status, source_list) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(
                    table_name)
                cursor.execute(sel_sql, source_id)
                exists_localtion = {}
                for id, localtion_id, source_list in cursor.fetchall():
                    print id, localtion_id, source_list
                    exists_localtion[localtion_id] = (id, json.loads(source_list or "{}"))

                new_hotels_and_not_id = []
                if exists_localtion:
                    for _i, line in enumerate(res_data):
                        new_hotels = {}
                        mylocaltion_id, myhotels = line[6], line[8]
                        if exists_localtion.has_key(mylocaltion_id):
                            yourid, yourhotels = exists_localtion[mylocaltion_id]
                            mykeys = myhotels.keys()
                            yourkeys = yourhotels.keys()
                            if len(mykeys) > len(yourkeys):
                                for k in mykeys:
                                    new_hotels[k] = myhotels.get(k) or yourhotels.get(k)
                            else:
                                for k in yourkeys:
                                    new_hotels[k] = yourhotels.get(k) or myhotels.get(k)

                            line[8] = json.dumps(new_hotels)
                            line.insert(0, yourid)
                        else:
                            line[8] = json.dumps(line[8] or {})
                            new_hotels_and_not_id.append(line)

                    res_data = filter(lambda x:len(x)==10, res_data)
                    cursor.executemany(rep_sql, res_data)
                    service_platform_conn.commit()

                if new_hotels_and_not_id:
                    cursor.executemany(ins_sql, new_hotels_and_not_id)
                    service_platform_conn.commit()
                if not exists_localtion:
                    for line in res_data:
                        line[8] = json.dumps(line[8])
                    cursor.executemany(ins_sql, res_data)
                    service_platform_conn.commit()

                cursor.close()
                service_platform_conn.close()
            except Exception as e:
                self.logger.exception(msg="[mysql error]", exc_info=e)
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        @func_time_logger
        def hotel_list_insert_db(table_name, res_data):
            try:
                service_platform_conn = service_platform_pool.connection()
                cursor = service_platform_conn.cursor()
                sql = "replace into {} (name, name_en, city_id, country_id, `from`, status, source_list) VALUES (%s,%s,%s,%s,%s,%s,%s)".format(
                    table_name)
                cursor.executemany(sql, res_data)
                service_platform_conn.commit()
                cursor.close()
                service_platform_conn.close()
            except Exception as e:
                self.logger.exception(msg="[mysql error]", exc_info=e)
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        if source == 'daodao':
            for hotel in hotel_result:
                name = hotel.get('hotel_name', '')
                name_en = hotel.get('hotel_name_en', '')
                localtion_id = hotel.get('localtion_id', '')
                hotels = hotel.get('hotels', {}).copy()
                if hotels in ('', None, 'NULL', 'null', {}):
                    status = 0
                else:
                    for k, v in hotels.iteritems():
                        if v not in ('', None, 'NULL', 'null', {}):
                            status = 1
                            break
                    else:
                        status = 0
                temp_save.append([name, name_en, city_id, country_id, 'daodao', source_id, localtion_id, status, hotels])

            hotel_list_insert_daodao(table_name, temp_save)

        elif source == 'google':
            for hotel in hotel_result:
                status = 1 if hotel_result else 0
                temp_save.append([name, name_en, city_id, country_id, 'google', source_id, 'localtion_id, ', status, json.dumps(hotel) if hotel else None])

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

        with MySession(need_cache=False, need_proxies=True) as session:
            resp_daodao = session.get(url)
            content_daodao = resp_daodao.text
            real_daodao_url = re.findall(r"redirectPage\('(.*)'\)", content_daodao)[0]

            # print content
            real_url = None
            print id, source, url
            # self.logger.info('%s\n%s\n%s\n' % (source, url, content[-600:]))
            try:
                if source == 'agoda':
                    url_obj = urlparse.urlsplit(real_daodao_url)
                    hid = urlparse.parse_qs(url_obj.query)['hid'][0]
                    line = SourceIDS.find_one({'source_id': 'agoda'+hid})
                    assert line, '没找到agoda的hid'
                    real_url = line['url']
                elif source == 'booking':
                    real_url = real_daodao_url.replace('http', 'https').replace('.html', '.zh-cn.html').split('?', 1)[0]
                elif source == 'ctrip':
                    base_url = 'http://hotels.ctrip.com/international/{0}.html'
                    url_obj = urlparse.urlsplit(real_daodao_url)
                    try:
                        hotel_id = urlparse.parse_qs(url_obj.query)['hotelid'][0]
                    except:
                        jumpUrl = urlparse.parse_qs(url_obj.query)['jumpUrl'][0]
                        hotel_id = re.findall('/name(\w+)', urlparse.urlsplit(jumpUrl).path)[0]
                    real_url = base_url.format(hotel_id)
                elif source == 'expedia':
                    raise Exception('我是expedia')
                elif source == 'hotels':
                    base_url = 'https://ssl.hotels.cn/ho'
                    url_obj = urlparse.urlsplit(real_daodao_url)
                    hotel_id = urlparse.parse_qs(url_obj.query)['hotelid'][0]
                    real_url = base_url + hotel_id
                else:
                    raise Exception('我是别的源')
            except:
                resp = session.get(real_daodao_url)
                content = resp.text

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
                    # hotel_id = re.search(r'hotelId":"([0-9]+)"', content).group(1)
                    hotel_id = re.search(r'data-hotelid="(\w+)"', content).group(1)

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
        sql = "update {0} set source_list = JSON_REPLACE(source_list, '$.{1}', %s) where id = %s".format(table_name, source);
        cursor.execute(sql, (real_url, id))
        service_platform_conn.commit()
        cursor.close()
        service_platform_conn.close()

        t3 = time.time()
        self.logger.info('入库耗时：   {}'.format(t3 - t2))

        self.task.error_code = 0
        return id, source, self.task.error_code


# class ConversionDaodaoURL2(BaseSDK):
#     def _execute(self, **kwargs):
#         id = kwargs['id']
#         source = kwargs['source']
#         url = kwargs['url']
#         table_name = kwargs['table_name']
#         t1 = time.time()
#         # url = url.replace('.cn', '.com')
#
#         with MySession(need_cache=False, need_proxies=True) as session:
#             # session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'})
#             resp_daodao = session.get(url)
#             content_daodao = resp_daodao.text
#             real_daodao_url = re.findall(r"redirectPage\('(.*)'\)", content_daodao)[0]
#             resp = session.get(real_daodao_url)
#             content = resp.text
#             # print content
#             real_url = None
#             print id, source, url
#             # self.logger.info('%s\n%s\n%s\n' % (source, url, content[-600:]))
#             if source == 'agoda':
#                 agoda_json = re.search(r'window.searchBoxReact = (.*)(?=;)', content).group(1)
#                 # root.xpath('//li[@data-selenium="hotel-item"]/a/@href')
#                 agoda_json = json.loads(agoda_json)
#                 url = agoda_json.get('recentSearches', [])[0].get('data', {}).get('url')
#                 base_url = 'https://www.agoda.com/zh-cn'
#                 real_url = ''.join([base_url, url])
#             elif source == 'booking':
#                 base_url = 'https://www.booking.com'
#                 root = html.fromstring(content)
#                 real_url = root.xpath('//div[@id="hotellist_inner"]//a')[0]
#                 real_url = ''.join([base_url, real_url.attrib.get('href').replace('-cn', '-com')])
#             elif source == 'ctrip':
#                 ctrip_json = re.search(r'hotelPositionJSON: (.*)(?=,)', content).group(1)
#                 ctrip_json = json.loads(ctrip_json)
#                 url = ctrip_json[0].get('url')
#                 base_url = "http://hotels.ctrip.com"
#                 real_url = ''.join([base_url, url])
#             elif source == 'elong':
#                 # hotel_id = re.search(r'hotelId":"([0-9]+)"', content).group(1)
#                 hotel_id = re.search(r'data-hotelid="(\w+)"', content).group(1)
#
#                 real_url = 'http://ihotel.elong.com/{0}/'.format(hotel_id)
#             elif source == 'expedia':
#                 raise Exception('我是expedia')
#             elif source == 'hotels':
#                 root = html.fromstring(content)
#                 hotel_id = root.xpath('//div[@id="listings"]//li')[0].attrib.get('data-hotel-id')
#                 real_url = "https://ssl.hotels.cn/ho{0}/?pa=1&q-check-out=2018-04-16&tab=description&q-room-0-adults=2&YGF=7&q-check-in=2018-04-15&MGT=1&WOE=1&WOD=7&ZSX=0&SYE=3&q-room-0-children=0".format(
#                     hotel_id)
# #
#         print real_url
#         t2 = time.time()
#         self.logger.info('抓取耗时：   {}'.format(t2 - t1))
#
#         service_platform_conn = service_platform_pool.connection()
#         cursor = service_platform_conn.cursor()
#         sql = "update {0} set source_list = JSON_REPLACE(source_list, '$.{1}', %s) where id = %s".format(table_name, source);
#         cursor.execute(sql, (real_url, id))
#         service_platform_conn.commit()
#         cursor.close()
#         service_platform_conn.close()
#
#         t3 = time.time()
#         self.logger.info('入库耗时：   {}'.format(t3 - t2))
#
#         self.task.error_code = 0
#         return id, source, self.task.error_code

if __name__ == "__main__":
    from proj.my_lib.Common.Task import Task as Task_to
    # url = "https://www.tripadvisor.cn/Hotels-g293938-Bandar_Seri_Begawan_Brunei_Muara_District-Hotels.html"
    # args = {
    #     'url': url,
    #     'source': 'daodao',
    #     'tag': '20180412a',
    #     'name': 'test_chinese',
    #     'name_en': 'test_english',
    #     'source_id': 'g123412',
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
        'id': 849181,
        'source': 'agoda',
        'url': 'https://www.tripadvisor.cn/Commerce?p=Agoda&src=81461442&geo=10050728&from=HotelDateSearch_Hotels&slot=1&matchID=1&oos=0&cnt=4&silo=6420&bucket=773150&nrank=2&crank=2&clt=D&ttype=DesktopMeta&tm=104044386&managed=false&capped=false&gosox=CvaPjKtz7l4roXnNkv8jgcAOJutXcprBxhol04L1AKIOBPvoigp2-Du3w6cUHylmM3Fi3w3DOfROZEM63ENuL1-uQAL2jKVZabFMKLgFfuDaOA5vDmHVJFCCj45WDzbOeRFPfzH54RPZAF4YcS4_gJMirYqcwaI0V0d7HyiOj1A&hac=AVAILABLE&mbl=BEAT&mbldelta=0&rate=171.32&fees=28.44&cur=RMB&adults=2&child_rm_ages=&inDay=29&outDay=30&rdex=RDEX_664f1b6faa3728243e71beb23f38f161&rooms=1&inMonth=4&inYear=2018&outMonth=4&outYear=2018&auid=6257a6a5-571c-42f1-845c-907a916d2150&def_d=true&cs=178b43491ab73d94c618ad4ee6e1c6079&area=QC_Meta|Chevron|Available|Main|Desktop&tp=Hotels_MainList&ob=new_tab&ik=4fef7ff1f3904fce902e47d5e6aa1df6&priceShown=200&aok=8e268bf504d64cdba152648743098b93',
        'table_name': 'list_result_daodao_20180412a',
    }

    task = Task_to(_worker='', _task_id='demo', _source='daodao', _type='suggest', _task_name='list_result_daodao_20180412a',
               _used_times=0, max_retry_times=6,
               kwargs=args, _queue='supplement_field',
               _routine_key='supplement_field', list_task_token='test', task_type=0, collection='')
    conversion = ConversionDaodaoURL(task)
    conversion.execute()