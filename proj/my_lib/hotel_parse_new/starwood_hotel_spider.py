# #coding:utf-8
# import time
# import datetime
# import json
# from lxml import etree
# import urllib
# import re
# from mioji.common import logger
# from mioji.common import parser_except
# from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
# from mioji.common.class_common import Hotel
# # from mioji.common.class_common import Hotel_New
# from proj.my_lib.models.HotelModel import HotelNewBase as Hotel_New
#
#
# class StarWoodSpider(Spider):
#     source_type = 'starwoodDetailHotel'
#     targets = {
#         'hotel': {}
#     }
#     old_spider_tag = {
#         'starwoodDetailHotel': {'required': ['room']}
#     }
#
#     def __init__(self, task=None):
#         self.item = {}
#         self.item['service'] = ''
#         self.hotel = Hotel_New()
#         super(StarWoodSpider, self).__init__(task)
#
#     def targets_request(self):
#
#         self.urls = self.task.content
#         if 'language=en_US' not in self.urls:
#             self.urls = self.urls + '&language=en_US'
#         self.id = re.compile(r'\d+').findall(self.urls.split('propertyID=')[-1])[0]
#         # print self.id
#
#         @request(retry_count=3, proxy_type=PROXY_REQ)
#         def crawl_info():
#             return {
#                 'req': {
#                     'url': self.urls,
#                     'method': 'get',
#                     'headers': {
#                         # 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
#                         # 'Host': 'www.starwoodhotels.com',
#                         # 'Cache-Control': 'max-age=0',
#                         # 'Referer': 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html'
#                         #            '?propertyID={}'.format(str(id)),
#                         # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 '
#                         #               '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
#                         # 'Upgrade-Insecure-Requests': 1,
#                         # 'Connection': 'keep-alive',
#                         # 'Content-Security-Policy': 'upgrade-insecure-requests'
#                     },
#
#                 },
#                 'user_handler': [self.parse_info],
#             }
#
#         yield crawl_info
#
#         @request(retry_count=3, proxy_type=PROXY_FLLOW)
#         def crawl_img():
#             return {
#                 'req': {
#                     'url': 'https://www.starwoodhotels.com/preferredguest/property/photos/index.html?propertyID={}'
#                            '&language=en_US'.format(str(self.id)),
#                     'method': 'get',
#                     'headers': {
#                         # 'Accept-Language': 'zh-CN,zh;q=0.9',
#                         # 'Host': 'www.starwoodhotels.com',
#                         # 'Cache-Control': 'max-age=0',
#                         # 'Referer': 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html'
#                         #            '?propertyID={}&language=en_US'.format(str(self.id)),
#                         # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 '
#                         #               '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
#                         # 'Upgrade-Insecure-Requests': 1,
#                         # 'Connection': 'keep-alive',
#                         # 'Content-Security-Policy': 'upgrade-insecure-requests'
#                     },
#
#                 },
#                 'user_handler': [self.parse_img],
#             }
#
#         yield crawl_img
#
#         @request(retry_count=3, proxy_type=PROXY_FLLOW)
#         def crawl_room():
#             return {
#                 'req': {
#                     'url': 'https://www.starwoodhotels.com/preferredguest/property/rooms/index.html?propertyID={}'
#                            '&language=en_US'.format(str(self.id)),
#                     'method': 'get',
#                     'headers': {
#                         # 'Accept-Language': 'zh-CN,zh;q=0.9',
#                         # 'Host': 'www.starwoodhotels.com',
#                         # 'Cache-Control': 'max-age=0',
#                         # 'Referer': 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html'
#                         #            '?propertyID={}&language=en_US'.format(str(self.id)),
#                         # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 '
#                         #               '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
#                         # 'Upgrade-Insecure-Requests': 1,
#                         # 'Connection': 'keep-alive',
#                         # 'Content-Security-Policy': 'upgrade-insecure-requests'
#                     },
#
#                 },
#                 'user_handler': [self.parse_room],
#             }
#
#         yield crawl_room
#
#         @request(retry_count=3, proxy_type=PROXY_FLLOW)
#         def crawl_map():
#             return {
#                 'req': {
#                     'url': 'https://www.starwoodhotels.com/preferredguest/property/area/directions.html?propertyID={}'
#                            '&language=en_US'.format(str(self.id)),
#                     'method': 'get',
#                     'headers': {
#                         # 'Accept-Language': 'zh-CN,zh;q=0.9',
#                         # 'Host': 'www.starwoodhotels.com',
#                         # 'Cache-Control': 'max-age=0',
#                         # 'Referer': 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html'
#                         #            '?propertyID={}&language=en_US'.format(str(self.id)),
#                         # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 '
#                         #               '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
#                         # 'Upgrade-Insecure-Requests': 1,
#                         # 'Connection': 'keep-alive',
#                         # 'Content-Security-Policy': 'upgrade-insecure-requests'
#                     },
#
#                 },
#                 'user_handler': [self.parse_map],
#             }
#
#         yield crawl_map
#
#         @request(retry_count=3, proxy_type=PROXY_FLLOW)
#         def crawl_traffic():
#             p = []
#             p.append({
#                 'req': {
#                     'url': 'https://www.starwoodhotels.com/preferredguest/property/area/transportation.html?propertyID={}'
#                            '&language=en_US'.format(str(self.id)),
#                     'method': 'get',
#                     # 'headers': {
#                     #     'Accept-Language': 'zh-CN,zh;q=0.9',
#                     #     'Host': 'www.starwoodhotels.com',
#                     #     'Cache-Control': 'max-age=0',
#                     #     'Referer': 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html'
#                     #                '?propertyID={}&language=en_US'.format(str(self.id)),
#                     #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 '
#                     #                   '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
#                     #     'Upgrade-Insecure-Requests': 1,
#                         # 'Connection': 'keep-alive',
#                         # 'Content-Security-Policy': 'upgrade-insecure-requests'
#                     # },
#
#                 },
#                 'user_handler': [self.parse_traffic],
#             })
#
#             return p
#
#         yield crawl_traffic
#
#         @request(retry_count=3, proxy_type=PROXY_FLLOW)
#         def crawl_policy():
#             return {
#                 'req': {
#                     'url': 'https://www.starwoodhotels.com/preferredguest/property/overview/announcements.html?'
#                            'propertyID={}&language=en_US'.format(str(self.id)),
#                     'method': 'get',
#                     'headers': {
#                         # 'Accept-Language': 'zh-CN,zh;q=0.9',
#                         # 'Host': 'www.starwoodhotels.com',
#                         # 'Cache-Control': 'max-age=0',
#                     # 'Referer': 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html'
#                     #            '?propertyID={}&language=en_US'.format(str(self.id)),
#                     #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 '
#                     #                   '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
#                     #     'Upgrade-Insecure-Requests': 1,
#                     # 'Connection': 'keep-alive',
#                     # 'Content-Security-Policy': 'upgrade-insecure-requests'
#                     },
#
#                 },
#                 'user_handler': [self.parse_policy],
#             }
#
#         yield crawl_policy
#
#
#
#
#         @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_hotel)
#         def crawl_service():
#             return {
#                 'req': {
#                     'url': 'https://www.starwoodhotels.com/preferredguest/property/features/index.html?propertyID={}'
#                            '&language=en_US'.format(str(self.id)),
#                     'method': 'get',
#                     'headers': {
#                         # 'Accept-Language': 'zh-CN,zh;q=0.9',
#                         # 'Host': 'www.starwoodhotels.com',
#                         # 'Cache-Control': 'max-age=0',
#                         # 'Referer': 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html'
#                         #            '?propertyID={}&language=en_US'.format(str(self.id)),
#                         # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 '
#                         #               '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
#                         # 'Upgrade-Insecure-Requests': 1,
#                         # 'Connection': 'keep-alive',
#                         # 'Content-Security-Policy': 'upgrade-insecure-requests'
#                     }
#
#                 },
#             }
#
#         yield crawl_service
#
#     def parse_info(self, req, resp):
#         node = etree.HTML(resp)
#         self.hotel.hotel_name = self.hotel.hotel_name_en = node.xpath('//span[@class="fn"]/text()')[0]
#         try:
#
#             street = node.xpath('//ul[@id="propertyAddress"]/li[contains(@class, "street-address")]/span/text()')[0]
#         except:
#             street = ''
#
#         try:
#             self.hotel.city = node.xpath('//ul[@id="propertyAddress"]/li[contains(@class, "city")]/span/text()')[0]
#             # print self.hotel.city
#         except:
#             self.hotel.city = 'NULL'
#         try:
#             self.hotel.country = node.xpath('//ul[@id="propertyAddress"]/li[contains(@class, "country")]/span/text()')[0]
#         except:
#             self.hotel.country = 'NULL'
#         try:
#             self.hotel.postal_code = node.xpath('//ul[@id="propertyAddress"]/li[contains(@class, "postal")]/span/'
#                                                   'text()')[0]
#
#             # print self.hotel.postal_code
#         except:
#             self.hotel.postal_code = 'NULL'
#
#         self.hotel.address = '{} {} {}'.format(self.hotel.country, self.hotel.city, street)
#         self.hotel.star = '5'
#         self.hotel.check_in_time = node.xpath('//span[@class="checkIn"]/text()')[0]
#         self.hotel.check_out_time = node.xpath('//span[@class="checkOut"]/text()')[0]
#
#
#         try:
#             description = node.xpath('//div[@class="quote"]/text()')[0]
#             self.hotel.description = description.replace('\r', '').replace('\n', '').strip()
#         except:
#             self.hotel.description = 'NULL'
#         try:
#             grade = node.xpath('//span[@class="ratingContainer"]/span/text()')
#             self.hotel.grade = grade[0]
#         except:
#             self.hotel.grade = 'NULL'
#
#         try:
#             phone = node.xpath('//ul[@id="propertyAddress"]/li[contains(@class, "phone")]/span/'
#                                   'text()')[0]
#             self.hotel.hotel_phone = phone.split(':')[-1]
#
#         except:
#             self.hotel.hotel_phone = 'NULL'
#
#
#     def parse_img(self, req, resp):
#         node = etree.HTML(resp)
#         img_list = node.xpath('//div[contains(@class, "imageSlide")]/div[contains(@class, "imageSlideContainer")]/'
#                               'div/@data-backgroundimage')
#
#         self.hotel.Img_first = 'https://www.starwoodhotels.com{}'.format(img_list[0])
#
#         self.hotel.img_items= '|'.join(['https://www.starwoodhotels.com{}'.format(img) for img in img_list])
#
#     def parse_room(self, req, resp):
#         node = etree.HTML(resp)
#         room_info_title = node.xpath('//div[@class="amenitiesContainer"]/div/h5')
#         room_info_content = node.xpath('//div[@class="amenitiesContainer"]/div/ul')
#
#         for room_title, room_content in zip(room_info_title, room_info_content):
#             title = room_title.xpath('./text()')[0]
#             content = ','.join(room_content.xpath('./li/text()'))
#             if 'pets' in title.lower():
#                 self.hotel.pet_type = content
#
#             if '24-Hour Room Service'.lower() in title.lower():
#                 self.hotel.service['Food_delivery'] = '24-Hour Room Service'
#             if 'Wake-up Service'.lower() in content.lower():
#                 self.hotel.service['wake'] = 'Service'
#
#
#     def parse_map(self, req, resp):
#         node = etree.HTML(resp)
#         try:
#             map_latitude = node.xpath('//div[@class="mapResults"]/div[@class="propertyList"]/'
#                                       'div[@class="property"]/@data-latitude')[0]
#             map_longitude = node.xpath('//div[@class="mapResults"]/div[@class="propertyList"]/'
#                                        'div[@class="property"]/@data-longitude')[0]
#         except:
#             raise parser_except.ParserException(22, '代理无效')
#
#         self.hotel.map_info = '{},{}'.format(map_longitude, map_latitude)
#
#     def parse_traffic(self, req, resp):
#
#         node = etree.HTML(resp)
#
#         data = node.xpath('//div[@id="modeContainer"]')[0]
#         infos = data.xpath('string(.)')
#         info = infos.replace('\n', '').replace('\t', '').replace('   ', '')
#         self.hotel.traffic = info
#
#     def parse_policy(self, req, resp):
#         # print resp
#         node = etree.HTML(resp)
#
#         policy_info_list = node.xpath('//div[@class="policy"]')
#         for policy_infos in policy_info_list[1:]:
#             policy_title_list = policy_infos.xpath('./div[contains(@class, "messageContainer")]/div/div[contains(@class, "persistentTitle")]/h4/text()')
#             policy_detail_list = policy_infos.xpath('./div[contains(@class, "messageContainer")]/div/div[contains(@class, "collapsibleDetails")]/p/text()')
#             for policy_title, policy_info in zip(policy_title_list, policy_detail_list):
#                 if 'Extra Bedding Policy'.lower() in policy_title.lower():
#                     self.hotel.chiled_bed_type = policy_info
#                 if 'Pet Policy'.lower() in policy_title.lower():
#                     self.hotel.pet_type = policy_info
#
#
#
#     def parse_service(self, resp):
#         node = etree.HTML(resp)
#         has_other = ','.join(node.xpath('//div[contains(@class, "persistentTitle")]/h4/text()'))
#         # print has_other
#         if "酒店设施" in has_other:
#             room_info_title = node.xpath('//div[@id="hotelFeatures"]/div/h5')
#             room_info_content = node.xpath('//div[@id="hotelFeatures"]/div/ul')
#
#             for room_title, room_content in zip(room_info_title, room_info_content):
#                 title = room_title.xpath('./text()')[0]
#                 content = ','.join(room_content.xpath('./li/text()'))
#                 self.item['service'] += '{}::{}|'.format(title, content)
#         if 'internet access' in has_other.lower():
#             wifi_info = node.xpath('//div[contains(@class, "internetAccessContainer")]/h5/text()')
#             wifi_info = [info.lower() for info in wifi_info]
#             # self.hotel.facility['Room_wifi'] = ''
#             # self.hotel.facility['Room_wired'] = ''
#             # self.hotel.facility['Pubic_wifi'] = ''
#             # self.hotel.facility['Public_wired'] = ''
#             # print wifi_info
#             if 'wired & wireless high speed internet access in guest rooms' in wifi_info:
#                 self.hotel.facility['Room_wifi'] = \
#                     self.hotel.facility['Room_wired'] = 'Wired & Wireless High Speed Internet Access in Guest Rooms'
#             if 'Wireless High Speed Internet Access'.lower() in wifi_info:
#                 self.hotel.facility['Room_wifi'] = 'Wireless High Speed Internet Access'
#             if 'Wired High Speed Internet Access'.lower() in wifi_info:
#                 self.hotel.facility['Room_wired'] = 'Wired High Speed Internet Access'
#             if 'Wireless High Speed Internet Access in Public Areas'.lower() in wifi_info:
#                 self.hotel.facility['Pubic_wifi'] = 'Wireless High Speed Internet Access in Public Areas'
#             if 'Wired High Speed Internet Access in Public Areas'.lower() in wifi_info:
#                 self.hotel.facility['Public_wired'] = 'Wired High Speed Internet Access in Public Areas'
#
#         room_info_content = node.xpath('//div[@id="noFeatureBoxesAmenitiesContainer"]/div/ul/li/text()')
#
#         content_list = [r.strip().replace(',', '') for r in room_info_content]
#
#         a = 1
#         for content in content_list:
#
#             content_lower = content.lower()
#             if 'Self'.lower() in content_lower and 'Parking'.lower() in content_lower:
#                 self.hotel.facility['Parking'] = content
#             if 'Free'.lower() in content_lower and 'Airport'.lower() in content_lower:
#                 self.hotel.facility['Airport_bus'] = content
#
#             if 'Pool'.lower() in content_lower:
#                 a += 1
#                 if a > 2:
#                     self.hotel.facility['Swimming_Pool'] += content
#                 else:
#                     self.hotel.facility['Swimming_Pool'] = content
#
#             if 'WestinWORKOUT® Fitness Studio'.lower() in content_lower:
#                 self.hotel.facility['gym'] = content
#             if 'Spa'.lower() in content_lower:
#                 self.hotel.facility['SPA'] = content
#             if 'Bar'.lower() in content_lower:
#                 self.hotel.facility['Bar'] = content
#             if 'Spa'.lower() in content_lower:
#                 self.hotel.facility['Mandara_Spa'] = content
#             if 'kids' in content_lower and 'club' in content_lower:
#                 self.hotel.facility['Recreation'] = content
#             if 'Business Center'.lower() in content_lower:
#                 self.hotel.facility['Business_Centre'] = content
#             self.hotel.facility['Restaurant'] = 'Restaurant'
#
#             if 'Concierge Desk'.lower() in content_lower:
#                 self.hotel.service['Protocol'] = content
#             if 'Copy'.lower() in content_lower or 'faxing' in content_lower:
#                 self.hotel.service['Fax_copy'] = content
#
#             if 'Shoe Shine Service'.lower() in content_lower:
#                 self.hotel.service['polish_shoes'] = content
#
#             if 'Laundry'.lower() in content_lower:
#                 self.hotel.service['Laundry'] = content
#
#             if 'Luggage'.lower() in content_lower:
#                 self.hotel.service['Luggage_Deposit'] = content
#
#     def parse_hotel(self, req, resp):
#         self.parse_service(resp)
#         self.hotel.city_id = self.id
#         self.hotel.source = 'starwood'.encode('utf-8')
#         self.hotel.source_id = self.id
#         self.hotel.brand_name = u'喜达屋'
#
#         self.hotel.star = '5'
#
#         self.hotel.review_num = 'NULL'
#
#         self.hotel.accepted_cards = 'NULL'
#
#         self.hotel.hotel_url = self.urls
#         self.hotel.continent = 'NULL'
#         self.hotel.other_info = []
#         res = json.loads(self.hotel.to_dict())
#         # print json.dumps(res, ensure_ascii=False)
#         # print res
#         return res
#
#
# if __name__ == "__main__":
#     from mioji.common.task_info import Task
#     from mioji.common.utils import simple_get_http_proxy
#     from mioji.common import spider
#     spider.slave_get_proxy = simple_get_http_proxy
#     task = Task()
#     spider = StarWoodSpider(task)
#
#     # task.content = 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html?propertyID=307' \
#     #                '&language=en_US'  # 酒店url
#     task.content = 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html?propertyID=1004&language=en_US'
#     spider.crawl()
#     print spider.code
#     print spider.result
#
