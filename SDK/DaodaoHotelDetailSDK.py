# coding=utf-8
import time
import pymongo
import requests
import pymongo.errors
from copy import deepcopy

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
import json

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


def parse_hotel_info(data):
    result = CommonHotel()
    key = data.keys()[0]
    info = data[key][0]
    result.hotel_name = info['hotel_name']
    result.hotel_name_en = info['hotel_name_en']
    result.source = info['source']
    result.source_id = info['source_id']
    result.source_city_id = ""
    result.brand_name = info['brand_name']
    result.map_info = info['map_info']
    result.address = info['address']
    result.city = info['city']
    result.country = info['country']
    result.city_id = ''
    result.postal_code = info['postal_code']
    result.star = info['star']
    result.grade = info['grade']
    result.review_num = info['review_num']
    result.has_wifi = info['has_wifi']
    result.is_wifi_free = info['is_wifi_free']
    result.has_parking = info['has_parking']
    result.is_parking_free = info['is_parking_free']
    result.service = info['service']
    result.img_items = info['img_items']
    result.description = info['description']
    result.accepted_cards = info['accepted_cards']
    result.check_in_time = info['check_in_time']
    result.check_out_time = info['check_out_time']
    result.hotel_url = info['hotel_url']
    result.continent = ''
    result.country_id = ''
    result.others_info = "{}"
    return result


class DaodaoHotelDetailSDK(BaseSDK):
    def _execute(self, **kwargs):
        url = self.task.kwargs['url']
        source = self.task.kwargs['source']
        source_id = self.task.kwargs['source_id']
        city_id = self.task.kwargs['city_id']
        country_id = self.task.kwargs['country_id']
        hid = self.task.kwargs['hid']

        headers = {}
        other_info = {
            'source_id': source_id,
            'city_id': city_id
        }

        if source in ['starwood', 'hyatt', 'gha','shangrila','fourseasons']:
            error_code, res, page_store_key_list = hotel_detail_database(url, source)

            if error_code == 0:
                result = parse_hotel_info(res)
            else:
                raise ServiceStandardError(error_code=error_code)
        else:
            with MySession(need_cache=True) as session:

                # booking start
                if source == 'booking':
                    headers['Referer'] = 'http://www.booking.com'

                # booking end

                session.headers.update(headers)
                start = time.time()
                if source not in ('hilton', 'ihg', 'holiday', 'accor', 'marriott'):
                    page = session.get(url, timeout=240)
                    page.encoding = 'utf8'
                    content = page.text
                elif source == 'ihg':
                    url1, url2 = url.split('#####')
                    page1 = session.get(url1, timeout=240)
                    page1.encoding = 'utf8'
                    content1 = page1.text

                    page2 = session.get(url2, timeout=240)
                    page2.encoding = 'utf8'
                    content2 = page2.text

                    content = [content1, content2]
                elif source == 'holiday':
                    url2, url1 = url.split('#####')
                    page1 = requests.get(url1, headers={'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                                                       'ihg-language': 'zh-CN'}, timeout=240)
                    page1.encoding = 'utf8'
                    content1 = page1.text

                    page2 = requests.get(url2, timeout=240, headers={
                        'accept': 'application/json, text/plain, */*',
                        'Content-Type': 'application/json; charset=UTF-8',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        'ihg-language': 'zh-CN',
                    })
                    page2.encoding = 'utf8'
                    content2 = page2.text

                    page3 = requests.get(url1, headers={'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y'}, timeout=240)
                    page3.encoding = 'utf8'
                    content3 = page3.text

                    content = (content1, content2, content3)
                elif source == 'accor':
                    proxy_url = "http://10.10.239.46:8087/proxy?source=pricelineFlight&user=crawler&passwd=spidermiaoji2014"
                    r = requests.get(proxy_url)
                    proxies = {'https': "socks5://" + str(r.text)}
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
                    }
                    page = requests.get(url, headers=headers, verify=False, proxies=proxies)
                    page.encoding = 'utf8'
                    content = page.text
                elif source == 'marriott':
                    url_list = url.split('#####')
                    url = url_list[0]

                    for i in url_list:
                        if len(i.split('=')) > 1:
                            key, value = i.split('=')[0], i.split('=')[1]
                            if key == 'longtitude':
                                other_info['longtitude'] = value
                            if key == 'latitude':
                                other_info['latitude'] = value
                        else:
                            if url_list.index(i) == 1:
                                other_info['hotel_name_en'] = i

                    url2 = url.replace("travel", "hotel-photos")
                    url3 = url.replace("travel/", "maps/travel/")
                    url4 = url.replace("hotels/", "hotels/fact-sheet/")
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0'
                    }
                    if "https://www.marriott.com" in url:
                        page1 = requests.get(url, headers=headers, timeout=240)
                        page2 = requests.get(url2, headers=headers, timeout=240)
                        page3 = requests.get(url3, headers=headers, timeout=240)
                        page4 = requests.get(url4, headers=headers, timeout=240)

                        page1.encoding = 'utf8'
                        page2.encoding = 'utf8'
                        page3.encoding = 'utf8'
                        page4.encoding = 'utf8'

                        content1 = page1.text
                        content2 = page2.text
                        content3 = page3.text
                        content4 = page4.text
                        content = (content1, content2, content3, content4)
                    else:
                        url2 = url + "/hotel-overview"
                        page1 = requests.get(url, headers=headers, timeout=240)
                        page2 = requests.get(url2, headers=headers, timeout=240)
                        page1.encoding = 'utf8'
                        page2.encoding = 'utf8'
                        content1 = page1.text
                        content2 = page2.text
                        content = (content1, content2)
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
            others_info = json.loads(result.others_info)
            others_info['hid'] = hid
            result.others_info = json.dumps(others_info)
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

if __name__ == "__main__":
    import requests
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Host': 'www.tripadvisor.cn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
    url = "https://ssl.hotels.cn/PPCHotelDetails?hotelid=113432&arrivalDate=15/04/2018&departureDate=16/04/2018&adultsPerRoom=2&numberOfRooms=1&pos=HCOM_CN&locale=zh_CN&rffrid=MDP.HCOM.DA.001.126.01.CNDAO-DM_B00.HSOWAj3.A.kwrd=TAIDWsHjosCoCwsAAHtruOoAAABI.ade=.mbl=L.sic=2.dd=0&wapa1=113432&PSRC=TRIP1&mpi=3125.20&mpj=462.53&mpg=RMB&mpk=T"
    response = requests.get(url)
    content = response.content
    print content
