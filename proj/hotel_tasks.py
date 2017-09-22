# coding=utf-8
import time
import re
import traceback
import datetime
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from copy import deepcopy
from proj.my_lib.Common.Browser import MySession
from proj.celery import app
from proj.my_lib.new_hotel_parser.hotel_parser import parse_hotel
from proj.my_lib.task_module.task_func import update_task
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.PageSaver import save_task_and_page_content
from my_lib.new_hotel_parser.data_obj import DBSession
from proj.my_lib.logger import get_logger
from sqlalchemy.sql import text

logger = get_logger("HotelDetail")
SQL = """replace into {table_name} (hotel_name, hotel_name_en, source, source_id, brand_name, map_info, address, city, \
country, city_id, postal_code, star, grade, review_num, has_wifi, is_wifi_free, has_parking, is_parking_free, service, \
img_items, description, accepted_cards, check_in_time, check_out_time, hotel_url, update_time, \
continent) values (:hotel_name, :hotel_name_en, :source, :source_id, :brand_name, :map_info, :address, :city, \
:country, :city_id, :postal_code, :star, :grade, :review_num, :has_wifi, :is_wifi_free, :has_parking, \
:is_parking_free, :service, :img_items, :description, :accepted_cards, :check_in_time, :check_out_time, :hotel_url, \
:update_time, :continent)"""


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='1/s')
def hotel_base_data(self, source, url, other_info, country_id, part, **kwargs):
    self.task_source = source.title()
    self.task_type = 'Hotel'
    self.error_code = 0
    sql = SQL.format(table_name = kwargs['task_name'])
    headers = {
        'User-agent': GetUserAgent()
    }

    with MySession(need_cache=True) as session:
        # hotels
        if source == 'hotels':
            hotel_id = re.findall('hotel-id=(\d+)', url)[0]
            url = 'http://zh.hotels.com/hotel/details.html?hotel-id=' + hotel_id

        # agoda 特殊情况 start
        # 转移 agoda 位置，防止 queue 挂掉

        # agoda end

        # hilton start
        # hilton end

        # venere start
        # if source == 'venere':
        #     update_task(kwargs['task_id'])

        # venere end

        # booking start
        if source == 'booking':
            headers['Referer'] = 'http://www.booking.com'

        # booking end

        session.headers.update(headers)

        # init session

        if source != 'hilton':
            page = session.get(url, timeout=240)
            page.encoding = 'utf8'
            content = page.text
        else:
            # headers['Upgrade-Insecure-Requests'] = '1'
            # headers['Cache-Control'] = 'max-age=0'
            # headers['Host'] = 'doubletree3.hilton.com'
            # session.headers.update(headers)
            session.auto_update_host = False
            hilton_index = url.find('index.html')
            if hilton_index > -1:
                url = url[:hilton_index]
            split_args = url.split('/')
            detail_url = 'http://www3.hilton.com/zh_CN/hotels/{0}/{1}/popup/hotelDetails.html'.format(
                split_args[-3], split_args[-2])
            map_info_url = url + 'maps-directions.html'
            desc_url = url + 'about.html'

            page = session.get(url)
            map_info_page = session.get(map_info_url)
            desc_page = session.get(desc_url)

            detail_page = session.get(detail_url, )
            page.encoding = 'utf8'
            detail_page.encoding = 'utf8'
            map_info_page.encoding = 'utf8'
            desc_page.encoding = 'utf8'
            __content = page.text
            logger.info(detail_url)
            __detail_content = detail_page.text
            __map_info_content = map_info_page.text
            __desc_content = desc_page.text

            content = [__content, __detail_content, __map_info_content, __desc_content]

        result = parse_hotel(content=content, url=url, other_info=other_info, source=source, part=part, retry_count=kwargs['retry_count'])

        try:
            result.country_id = country_id
            result.update_time = datetime.datetime.now()
            logger.info(str(result.__dict__))
            session = DBSession()
            session.execute(text(SQL.format(table_name=kwargs['task_name'])), [result.__dict__])
            session.commit()
            session.close()
        except Exception as e:
            self.error_code = 33
            logger.exception(e)
            raise e

        # if not result:
        #     raise Exception('db error')
        # else:
        #     if type(content) is list:
        #         contents = content
        #     else:
        #         contents = [content]
        #     for content_ in contents:
        #         if kwargs.get('mongo_task_id'):
        #             # 保存抓取成功后的页面信息
        #             save_task_and_page_content(task_name=part, content=content_, task_id=kwargs['mongo_task_id'],
        #                                        source=source,
        #                                        source_id=other_info['source_id'],
        #                                        city_id=other_info['city_id'], url=url)

        return result.__dict__
