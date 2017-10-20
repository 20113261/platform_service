# coding=utf-8
import time
from util.UserAgent import GetUserAgent

from proj.my_lib.Common.Browser import MySession
from proj.celery import app
from proj.my_lib.new_hotel_parser.hotel_parser import parse_hotel
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.logger import get_logger
from proj.mysql_pool import service_platform_pool

logger = get_logger("HotelDetail")


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='8/s')
def hotel_base_data(self, source, url, other_info, country_id, part, **kwargs):
    task_response = kwargs['task_response']
    task_response.source = source.title()
    task_response.type = 'Hotel'

    headers = {
        'User-agent': GetUserAgent()
    }

    with MySession(need_cache=True, do_not_delete_cache=True) as session:
        # hotels
        if source == 'hotels':
            url = 'https://zh.hotels.com/ho{0}/'.format(other_info['source_id'])
            # hotel_id = re.findall('hotel-id=(\d+)', url)
            # if hotel_id:
            #     url = 'https://zh.hotels.com/ho{0}/'.format(hotel_id[0])
            # else:

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
        start = time.time()
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
        logger.debug("[crawl_data][Takes: {}]".format(time.time() - start))

        start = time.time()
        result = parse_hotel(content=content, url=url, other_info=other_info, source=source, part=part,
                             retry_count=kwargs['retry_count'])
        logger.debug("[parse_hotel][func: {}][Takes: {}]".format(parse_hotel.func_name, time.time() - start))

        start = time.time()
        try:
            service_platform_conn = service_platform_pool.connection()
            cursor = service_platform_conn.cursor()
            sql = result.generation_sql()
            sql = sql.format(table_name=kwargs['task_name'])
            values = result.values()
            print result.__dict__
            cursor.execute(sql, values)
            service_platform_conn.commit()
            cursor.close()
            service_platform_conn.close()
        except Exception as e:
            task_response.error_code = 33
            logger.exception(e)
            raise e

        logger.debug("[Insert DB][Takes: {}]".format(time.time() - start))

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
        task_response.error_code = 0
        return task_response.error_code
