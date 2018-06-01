# coding=utf-8
import time
import pymongo
import requests
import pymongo.errors
from copy import deepcopy
import re

from mioji.spider_factory import factory
from mioji.common.task_info import Task
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.list_config import cache_config, none_cache_config
from proj.my_lib.logger import get_logger
from proj.my_lib.new_hotel_parser.hotel_parser import parse_hotel
from proj.mysql_pool import service_platform_pool
from mongo_pool import mongo_data_client
from proj.my_lib.models.HotelModel import CommonHotel


logger = get_logger("HotelDetailSDK")


def hotel_detail_database(url, source, need_cache=True):
    task = Task()
    task.content = url
    spider = factory.get_spider_by_old_source(source + 'DetailHotel')
    spider.task = task
    spider.task.source = source
    if need_cache:
        error_code = spider.crawl(required=['hotel'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['hotel'], cache_config=none_cache_config)
    logger.info(str(task.ticket_info) + '  --  ' + task.content + '--' + str(error_code))
    return error_code, spider.result, spider.page_store_key_list


class MyHotelDetailSDK(BaseSDK):
    def _execute(self, **kwargs):
        url = self.task.kwargs['hotel_url']
        source = self.task.kwargs['source']
        source_id = self.task.kwargs['source_id']
        city_id = self.task.kwargs['city_id']
        country_id = self.task.kwargs['country_id']

        headers = {}
        other_info = {
            'source_id': source_id,
            'city_id': city_id,
        }
        logger.debug('aaaaaaa  '+source)
        logger.debug('bbbbbbb  '+str(source in ['starwood', 'hyatt', 'gha','shangrila','fourseasons','bestwest']))
        if source in ['starwood', 'hyatt', 'shangrila','fourseasons', 'bestwest']:
            error_code, res, page_store_key_list = hotel_detail_database(url, source)

            if error_code == 0:
                result = parse_hotel_info(res)
            else:
                raise ServiceStandardError(error_code=error_code)
        else:
            with MySession(need_cache=True) as session:
                start = time.time()
                # hotels
                if source == 'hilton':
                    url = url.replace('index.html', '')
                    detail_url = 'http://www3.hilton.com/zh_CN/hotels/china/{}/popup/hotelDetails.html'.format(
                        url.split('/')[-2])
                    enDetail_url = 'http://www3.hilton.com/en/hotels/{}/{}/about/amenities.html'.format(
                        url.split("/")[-3], url.split("/")[-2])
                    map_info_url = url + 'maps-directions.html'
                    desc_url = url + 'about.html'
                    session = requests.session()
                    content = session.get(url).text
                    detail_content = session.get(detail_url).text
                    map_info_content = session.get(map_info_url).text
                    desc_content = session.get(desc_url).text
                    enDetail = session.get(enDetail_url)
                    enDetail.encoding = 'utf8'
                    enDetail_content = enDetail.text
                    other_info = {
                        'source_id': '1000',
                        'city_id': '50795'
                    }
                    content = [content, map_info_content, desc_content, enDetail_content]

                logger.debug("[crawl_data][Takes: {}]".format(time.time() - start))



                start = time.time()
                result = parse_hotel(content=content, url=url, other_info=other_info, source=source,
                                     part=self.task.task_name,
                                     retry_count=self.task.used_times)
                logger.debug("[parse_hotel][func: {}][Takes: {}]".format(parse_hotel.func_name, time.time() - start))

        try:
            data_collections = mongo_data_client['ServicePlatform'][self.task.task_name]
            data_collections.create_index([('source', 1), ('source_id', 1)], unique=True, background=True)
            data_collections.create_index([('location', '2dsphere')], background=True)
            tmp_result = deepcopy(result.values(backdict=True))
            lon, lat = str(result.map_info).split(',')
            lon, lat = float(lon), float(lat)
            tmp_result.update(
                {
                    'location': {
                        'type': "Point",
                        'coordinates': [lon, lat]
                    }
                }
            )
            data_collections.save(tmp_result)
        except pymongo.errors.DuplicateKeyError:
            # logger.exception("[result already in db]", exc_info=e)
            logger.warning("[result already in db]")
        except Exception as exc:
            raise ServiceStandardError(error_code=ServiceStandardError.MONGO_ERROR, wrapped_exception=exc)

        start = time.time()
        try:
            service_platform_conn = service_platform_pool.connection()
            cursor = service_platform_conn.cursor()
            sql = result.generation_sql()
            sql = sql.format(table_name=self.task.task_name)
            values = result.values()
            # self.logger.info(result.__dict__)
            cursor.execute(sql, values)
            service_platform_conn.commit()
            cursor.close()
            service_platform_conn.close()
        except Exception as e:
            self.logger.exception(e)
            raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        logger.debug("[Insert DB][Takes: {}]".format(time.time() - start))
        self.task.error_code = 0
        return self.task.error_code
