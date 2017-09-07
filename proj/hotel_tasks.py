# coding=utf-8
import time
import re
import traceback
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent

from proj.my_lib.Common.Browser import MySession
from proj.celery import app
from proj.my_lib.new_hotel_parser.hotel_parser import parse_hotel
from proj.my_lib.task_module.task_func import update_task
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.PageSaver import save_task_and_page_content
from my_lib.new_hotel_parser.data_obj import DBSession
from proj.my_lib.logger import get_logger

logger = get_logger("HotelDetail")


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='8/s')
def hotel_base_data(self, source, url, other_info, part, **kwargs):
    self.task_source = source.title()
    self.task_type = 'Hotel'
    self.error_code = 0

    headers = {
        'User-agent': GetUserAgent()
    }

    with MySession() as session:
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
            headers['Upgrade-Insecure-Requests'] = '1'
            headers['Cache-Control'] = 'max-age=0'
            headers['Host'] = 'doubletree3.hilton.com'
            session.headers.update(headers)
            hilton_index = url.find('index.html')
            if hilton_index>-1:
                url = url[:hilton_index]
            detail_url = 'http://www3.hilton.com/zh_CN/hotels/china/{}/popup/hotelDetails.html'.format(
                url.split('/')[-2])
            map_info_url = url + 'maps-directions.html'
            desc_url = url + 'about.html'

            page = session.get(url)
            __content = page.text
            logger.info(detail_url)
            __detail_content = session.get(detail_url).text
            __map_info_content = session.get(map_info_url).text
            __desc_content = session.get(desc_url).text

            content = [__content, __detail_content, __map_info_content, __desc_content]

        result = parse_hotel(content=content, url=url, other_info=other_info, source=source, part=part)

        try:
            session = DBSession()
            session.merge(result)
            session.commit()
            session.close()
        except Exception as e:
            self.error_code = 33
            logger.exception(e)
            raise e


        if not result:
            raise Exception('db error')
        else:
            if type(content) is list:
                contents = content
            else:
                contents = [content]
            for content_ in contents:
                if kwargs.get('mongo_task_id'):
                    # 保存抓取成功后的页面信息
                    save_task_and_page_content(task_name=part, content=content_, task_id=kwargs['mongo_task_id'], source=source,
                                               source_id=other_info['source_id'],
                                               city_id=other_info['city_id'], url=url)

        return result.__dict__
