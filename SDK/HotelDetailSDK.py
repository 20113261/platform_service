# coding=utf-8
import time

from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.logger import get_logger
from proj.my_lib.new_hotel_parser.hotel_parser import parse_hotel
from proj.mysql_pool import service_platform_pool

logger = get_logger("HotelDetailSDK")


class HotelDetailSDK(BaseSDK):
    def _execute(self, **kwargs):
        url = self.task.kwargs['url']
        source = self.task.kwargs['source']
        source_id = self.task.kwargs['source_id']
        city_id = self.task.kwargs['city_id']
        country_id = self.task.kwargs['country_id']

        headers = {}

        with MySession(need_cache=True, do_not_delete_cache=True) as session:
            # hotels
            if source == 'hotels':
                url = 'https://zh.hotels.com/ho{0}/'.format(source_id)

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

            other_info = {
                'source_id': source_id,
                'city_id': city_id
            }

            start = time.time()
            result = parse_hotel(content=content, url=url, other_info=other_info, source=source,
                                 part=self.task.task_name,
                                 retry_count=self.task.used_times)
            logger.debug("[parse_hotel][func: {}][Takes: {}]".format(parse_hotel.func_name, time.time() - start))

            start = time.time()
            try:
                service_platform_conn = service_platform_pool.connection()
                cursor = service_platform_conn.cursor()
                sql = result.generation_sql()
                sql = sql.format(table_name=self.task.task_name)
                values = result.values()
                self.logger.info(result.__dict__)
                cursor.execute(sql, values)
                service_platform_conn.commit()
                cursor.close()
                service_platform_conn.close()
            except Exception as e:
                logger.exception(e)
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

            logger.debug("[Insert DB][Takes: {}]".format(time.time() - start))
            self.task.error_code = 0
            return self.task.error_code

