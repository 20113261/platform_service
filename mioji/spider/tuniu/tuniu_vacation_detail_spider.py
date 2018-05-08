#!/usr/bin/env python
# coding:utf-8

"""
@File: tuniu_vacation_detail_spider.py
@License: Private@Mioji
@Author: Wang Xinyong
@E-mail: wangxinyong@mioji.com
@Time: 18/1/29 下午3:40
"""
import time
import base64
import re
import copy
from datetime import datetime, timedelta
from lxml import etree
import lxml
from mioji.common.spider import Spider
from mioji.common.spider import request, PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
from mioji.common.parser_except import ParserException
from tuniu_parser import Utils as tools
from tuniu_parser import extract_index_json
import HTMLParser
from tuniu_parser import VacationModel, RouteModel, HotelModel, TourModel
import json
import requests

class TuniuVacationSpider(Spider):
    source_type = 'tuniu|vacation_detail'
    targets = {'vacation': {}}
    old_spider_tag = {
            'tuniu|vacation_detail': {'required': ['detail']}
            }

    def __init__(self):
        super(TuniuVacationSpider, self).__init__()
        self.calen_tour_url = ('http://www.tuniu.com/tour/api/calendar?productId={product_id}&'
                               'bookCityCode={search_city_code}&departCityCode={dept_city_code}&'
                               'backCityCode={back_city_code}')
        self.calen_pro_url = ('http://www.tuniu.com/product/api/pkg?productId={product_id}'
                              '&departCityCode={dept_city_code}')

        self.supplier_url = ('http://www.tuniu.com/papi/product/aggregation?supplier=1'
                             '&productId={product_id}')

        # 缺省行程的信息在HTML列表中
        self.journey_tour_url_template = ('http://www.tuniu.com/tour/api/journeyInfo?productId={product_id}&'
                                          'journeyId={journey_id}&bookCity={search_city_code}&departCity='
                                          '{dept_city_code}&backCity={back_city_code}')
        self.journey_pro_url_template = ('http://www.tuniu.com/product/api/journey?productId={product_id}&'
                                         'journeyId={journey_id}')
        self.visa_url_template = 'http://www.tuniu.com/papi/product/visa/{product_id}/200/200'

        self.temp_types = ('tour', 'product')
        self.temp_type = self.temp_types[0]
        self.pub_meta = dict()  # 存储同一ID下公用的元信息
        self.journey_meta_data = list()  # 存储每个行程元信息
        self.result_list = list()
        self.date_limit = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
        #self.rec_type()
        self.extra_traffic = 0
        self.extra_city = list()
        self.child_standard = ''
        self.is_multi_city = "no"
        self.multi_city = []
        self.plan_date = list()    # a moot test field

    def rec_type(self):
        flag = True
        for index, value in enumerate(self.temp_types):
            if value in self.index_url:
                self.temp_type = value
                flag = False
                break
        if flag:
            raise Exception

    def targets_request(self):
        self._task = self.task.ticket_info.get('vacation_info', [])
        self.index_url = self._task['url']
        self.rec_type()
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def extra_city_request():
            """请求数据"""
            return {
                'req': {
                    'url': self.index_url,
                    'method': 'get'
                },
                'data': {'content_type': 'xml'},
                'user_handler': [self.parse_extra_city]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def multi_city_request():
            """请求数据"""
            return {
                'req': {
                    'url': self.index_url,
                    'method': 'get'
                },
                'data': {'content_type': 'xml'},
                'user_handler': [self.parse_multi_city]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def index_request():
            """请求主页，获取基础元信息"""
            # print('index_request', self.index_url)
            return {
                'req': {
                    'url': self.index_url,
                    'cookies': {'tuniuuser_citycode': base64.b64encode(self._task['search_dept_city_id'])},
                    'method': 'get',
                },
                'data': {'content_type': 'xml'},
                'user_handler': [self.parse_index]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ, new_session=True)
        def tour_calender_request():
            """请求日历接口"""
            # print('tour_calender_request', self.calen_tour_url.format(product_id=self._task['id'],
            #                                           search_city_code=self._task['search_dept_city_id'],
            #                                           dept_city_code=self.pub_meta['dept_city_code'],
            #                                           back_city_code=self.pub_meta['back_city_code']))
            return {
                'req': {
                    'url': self.calen_tour_url.format(product_id=self._task['id'],
                                                      search_city_code=self._task['search_dept_city_id'],
                                                      dept_city_code=self.pub_meta['dept_city_code'],
                                                      back_city_code=self.pub_meta['back_city_code']),
                    'method': 'get',
                },
                'data': {'content_type': 'json'},
                'user_handler': [self.parse_calender]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def pro_calender_request():
            """请求日历接口"""
            # print(self.calen_pro_url.format(product_id=self._task['id'],
            #                           dept_city_code=''))
            return {
                'req': {
                    'url': self.calen_pro_url.format(product_id=self._task['id'],
                                      dept_city_code=''),
                    'method': 'get',
                },
                'data': {'content_type': 'json'},
                'user_handler': [self.parse_calender]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def tour_supplier_request():
            """供应商信息"""
            # print('tour_supplier_request', self.supplier_url.format(product_id=self._task['id']))
            return {
                'req': {'url': self.supplier_url.format(product_id=self._task['id']),
                        'method': 'get'},
                'data': {'content_type': 'json'}, 'user_handler': [self.parse_supplier]}

        @request(retry_count=3, proxy_type=PROXY_FLLOW, async=True)
        def multi_journey_request():
            """其余套餐/线路请求"""
            pages_map = dict()
            pages_map.setdefault(self.temp_type, list())
            # 除第一程之外的行程信息
            for index, journey in enumerate(self.journey_meta_data[1:]):
                if self.temp_type == self.temp_types[0]:
                    url = self.journey_tour_url_template.format(product_id=self._task['id'],
                                                                journey_id=journey['id'],
                                                                search_city_code=self._task['search_dept_city_id'],
                                                                dept_city_code=self._task['search_dept_city_id'],
                                                                back_city_code=self.pub_meta['back_city_code'])

                else:
                    url = self.journey_pro_url_template.format(product_id=self._task['id'],
                                                               journey_id=journey['id'])
                # print('multi_journey_request', url)
                pages_map[self.temp_type].append({
                    'req': {'url': url, 'method': 'get', },
                    'field_need': {'id': journey['id'], 'index': index + 1},
                    'data': {'content_type': 'json'},
                    'user_handler': [self.parse_journey]
                })

            return pages_map[self.temp_type]

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_vacation)
        def visa_request():
            # print('visa_request', self.visa_url_template.format(product_id=self._task['id']))
            return {
                'req': {
                    'url': self.visa_url_template.format(product_id=self._task['id']),
                    'method': 'get', }, 'data': {'content_type': 'json'}, 'user_handler': [self.parse_visa]
            }

        request_map = {
            self.temp_types[0]: [index_request, tour_calender_request, tour_supplier_request,
                                 multi_journey_request, visa_request],
            self.temp_types[1]: [index_request, pro_calender_request, multi_journey_request, visa_request]
        }

        for index, req in enumerate(request_map[self.temp_type]):
            yield req

    def parse_extra_city(self, resp):
        try:
            city_list = list()
            dict_data = re.findall(r'window.pageData = (\{.+?\})\;', resp, re.S)[0]
            dict_data = re.findall(r'connection: (\{.+\})\,', dict_data)[0]
            json_data = json.loads(dict_data)
            if json_data.get('connectCityList', list()):
                for each in json_data.get('connectCityList', list()):
                    city_list.extend(each.get('cityList', list()))

            self.extra_traffic = json_data.get('isSupportConnection', 0)
            self.extra_city = city_list
        except:
            pass
        # print(self.extra_traffic)
        # print(self.extra_city)

    def parse_multi_city(self, resp):
        city_list = list()
        # parser = HTMLParser.HTMLParser()
        # resp = parser.unescape(lxml.html.tostring(resp))

        str_data = re.findall(r'window.pageData = (\{.+?\})\;', resp, re.S)[0]
        str_data = re.findall(r'departCityList: (\[\{.+\}\])\,', str_data)
        if str_data:
            json_list = json.loads(str_data[0])
            for each in json_list:
                dict_ = {
                    'city_id': each.get('code'),
                    'city_name': each.get('name'),
                    'price': each.get('price')
                }
                city_list.append(dict_)

            if len(city_list) > 1:
                self.is_multi_city = 'yes'
            self.multi_city = city_list
        else:
            str_data = re.findall(r'window.baseData = (\{.+?\})\;', resp, re.S)[0]
            str_data = re.findall(r'citiesList":(\[\{.+?\]\}\])\,', str_data)
            if str_data:
                json_list = json.loads(str_data[0])
                for i in json_list:
                    j = i['cityList']
                    for each in j:
                        dict_ = {
                            'city_id': each.get('cityCode'),
                            'city_name': each.get('cityName'),
                            'price': each.get('startPrice')
                        }
                        city_list.append(dict_)

            if len(city_list) > 1:
                self.is_multi_city = 'yes'
            self.multi_city = city_list
        # print(self.is_multi_city)
        # print(self.multi_city)

    def parse_index(self, req, resp):
        """ 解析详情首页HTML
            1、获取产品经理推荐
            2、产品亮点
            3、轮播图
            4、行程索引
            5、获取搜索预定城市、目的地城市、成团出发城市。（name&code）
            6、星级
            7、获取产品名称
        """

        def parse_tour(req, resp):
            self.parse_extra_city(resp)
            self.parse_multi_city(resp)
            xml_obj = etree.HTML(resp)
            self.pub_meta['highlight'] = map(lambda x: x.strip(),
                                             xml_obj.xpath('//*[@class="resource-recommend-tag"]/text()'))

            _recommend = re.findall(
                r'<div.*?id=\"J_ResourceRecommend\".*?>.*?<div.*?class=\"resource-recommend-content-inner\".*?>(.+?)</div>',
                resp, re.S)[0]
            # _recommend = xml_obj.xpath(
            #     '//div[@id="J_ResourceRecommend"]//div[@class="resource-recommend-content-inner"]/text()')
            self.pub_meta['recommend'] = _recommend.strip()
            # self.pub_meta['recommend'] = '<br>'.join(map(tools.unescape, _recommend)).strip()

            self.pub_meta['img_list'] = map(lambda x: x.strip(),
                                            xml_obj.xpath(('//div[@class="gallery-video-cover"]//img/@src | '
                                                           '//li[@class="gallery-photo"]//img/@src ')))

            dept_city = ''.join(xml_obj.xpath('//div[@class="resource-city-more-selected"]/text()'))
            if '（' in dept_city:
                dept_city = dept_city.split('（')[0]
            try:
                self.pub_meta['dept_city'] = dept_city.split('\n')[-1].strip(' ')
            except:
                self.pub_meta['dept_city'] = dept_city
            js_data = extract_index_json(resp)
            self.pub_meta['book_city_code'] = js_data.get('bookCityCode', '')
            self.pub_meta['dept_city_code'] = js_data.get('departCityCode', '')
            self.pub_meta['back_city_code'] = js_data.get('backCityCode', '')
            self.pub_meta['back_city_name'] = js_data.get('backCityName', '')
            self.pub_meta['team_city_name'] = js_data.get('teamCityName', '')
            self.pub_meta['dest_city_name'] = js_data.get('destination', '')

            self.pub_meta['name'] = xml_obj.xpath('//h1/strong/text()')[0]

            multi_journey = js_data.get('multiJourneyBaseInfos')
            date_list = requests.get(self.calen_tour_url.format(product_id=self._task['id'],
                                                                search_city_code=self._task['search_dept_city_id'],
                                                                dept_city_code=self.pub_meta['dept_city_code'],
                                                                back_city_code=self.pub_meta['back_city_code'])).text
            date_list = json.loads(date_list)
            date_list = date_list.get('data', {}).get('roomAddBudget', {}).keys()
            for journey in multi_journey:
                one = dict()
                one['id'] = journey['journeyId']
                one['name'] = journey['journeyName']
                one['resid'] = journey['resId']
                one['day'] = journey['dayDuration']
                one['night'] = journey['nightDuration']
                j_plan_date = journey['planDate']
                if j_plan_date:
                    one['suit_date'] = {date: {} for date in journey['planDate']}  # None lead to 29 code error
                else:
                    one['suit_date'] = {date: {} for date in date_list}
                self.journey_meta_data.append(one)
            self.plan_date = journey['planDate'] or date_list
            star_items = xml_obj.xpath('//a[@id="J_basisStar"]/i')
            self.pub_meta['star_level'] = len(star_items)

            self.parse_journey(req, resp)

        def parse_pro(req, resp):
            self.parse_extra_city(resp)
            self.parse_multi_city(resp)
            xml_obj = etree.HTML(resp)
            js_data = extract_index_json(resp)

            self.pub_meta['img_list'] = xml_obj.xpath('//div[@id="J_Gallery"]/div[@class="display"]//img/@src')

            _recommend = []
            self.pub_meta['recommend'] = '<br>'.join(map(tools.unescape, _recommend)).strip()

            self.pub_meta['book_city_code'] = js_data.get('bookCityCode', '')
            self.pub_meta['dept_city_code'] = js_data.get('departCityCode', '')
            self.pub_meta['back_city_code'] = js_data.get('backCityCode', '')
            self.pub_meta['back_city_name'] = js_data.get('backCityName', '')
            self.pub_meta['team_city_name'] = js_data.get('teamCityName', '')
            self.pub_meta['dest_city_name'] = js_data.get('destination', '')

            self.pub_meta['name'] = xml_obj.xpath('//h1/strong/text()')[0]

            brand = xml_obj.xpath('//div[@class="head-shop-title"]/a/text()')
            brand = ''.join(brand)
            # 品牌
            self.pub_meta['brand'] = brand
            # 公司全称
            supplier = ''.join(xml_obj.xpath('//span[@class="vendor"]/text()'))
            supplier = ''.join(re.findall(ur'本产品由(.*?公司)', supplier))

            multi_journey = js_data.get('journeyInfos')
            for journey in multi_journey:
                one = dict()
                one['id'] = journey['journeyId']
                one['name'] = journey['journeyName']
                one['brand'] = brand
                one['supplier'] = supplier
                one['suit_date'] = dict()
                self.journey_meta_data.append(one)

            # 亮点
            highlight = xml_obj.xpath(('//div[@class="head-section-item head-feature-point"]//'
                                               'div[@class="head-feature-point-item"]/text()'))

            dept_city = ''.join(xml_obj.xpath('//div[@class="resource-city-more-selected"]/text()')).replace('（', '')

            self.pub_meta['highlight'] = highlight
            try:
                self.pub_meta['dept_city'] = dept_city.split('\n')[-1].strip(' ')
            except:
                self.pub_meta['dept_city'] = dept_city
            # 是否需要再次确认
            # confirm_again = xml_obj.xpath(('//div[@class="m-head-section m-head-feature"]//'
            #                                'div[@class="head-section-content"]/text()'))
            # maybe_len = len(filter(lambda x: x.startswith('需要二次确认'),
            #                        map(lambda x: x.strip(), confirm_again)))
            # confirm_again = 0 if maybe_len > 0 else 1
            # self.pub_meta['confirm'] = confirm_again

            # 星级
            star_items = xml_obj.xpath('//a[@id="J_basisStar"]/i')
            self.pub_meta['star_level'] = len(star_items)

            self.parse_journey(req, resp)

        parser_map = {
            self.temp_types[0]: parse_tour,
            self.temp_types[1]: parse_pro
        }
        parser_map[self.temp_type](req, resp)

    def parse_calender(self, req, resp):
        """解析日历接口信息"""

        def parse_tour(req, resp):
            if 0 != resp.get('code'):
                raise Exception
            cal_list = resp['data'].get('calendars', [])
            room_budget = resp['data'].get('roomAddBudget', [])
            date_list = []
            for cal in cal_list:
                date = cal.get('departDate')
                if date > self.date_limit:
                    continue
                one_date = dict(date=date,
                                adult_price=cal.get('adultMarketPrice'),
                                child_price=cal.get('childPrice'),
                                adult_rest=cal['stockInfo'].get('stockNum', 0),
                                child_rest=0,
                                deadline_date=cal.get('deadLineTime', '')[:10] if cal.get('deadLineTime', '') else '',
                                book_pre=cal.get('deadLineDate', 0),
                                room_fee=room_budget.get(date, 0))

                date_list.append(one_date)
            for index, journey in enumerate(self.journey_meta_data):
                _suit_date = journey['suit_date']
                for date in date_list:
                    if date['date'] in journey['suit_date'].keys():
                        _suit_date[date['date']].update(date)
                self.journey_meta_data[index]['suit_date'].update(_suit_date)

        def parse_pro(req, resp):

            if 0 != resp.get('code'):
                raise Exception
            room_fee_type = resp.get('data').get('priceMethod').get('diffRoomPriceMethod')
            if '单房差现询' == room_fee_type:
                room_fee_type = False
            else:
                room_fee_type = True
            pack_list = resp.get('data').get('packageList', [])

            for index, pack in enumerate(pack_list):
                is_dept_city = pack.get('departCityList')
                if is_dept_city:
                    is_dept_city = is_dept_city[0].get('cityCode')
                if is_dept_city == self.pub_meta['dept_city_code'] or not is_dept_city:

                    cal_list = pack.get('priceCalendarList')
                    book_pre = pack.get('bookDay')
                    for cal in cal_list:
                        date = cal.get('departDate')
                        if date > self.date_limit:
                            continue
                        fmt = '%Y-%m-%d'
                        deadline = (datetime.strptime(date, fmt) - timedelta(days=book_pre)).strftime(fmt)
                        room_fee = cal.get('diffRoomPrice', 0.0) if room_fee_type else 0.0
                        one_date = dict(date=date,
                                        adult_price=cal.get('adultPrice'),
                                        child_price=cal.get('childPrice'),
                                        adult_rest=cal.get('adultStock'),
                                        child_rest=cal.get('childStock'),
                                        deadline_date=deadline,
                                        book_pre=book_pre,
                                        room_fee=room_fee
                                        )

                        self.journey_meta_data[0]['suit_date'].update({date: one_date})
        parser_map = {
            self.temp_types[0]: parse_tour,
            self.temp_types[1]: parse_pro
        }
        parser_map[self.temp_type](req, resp)

    def parse_journey(self, req, resp):
        """解析行程"""

        def parse_first_journey(req, resp):
            self.journey_meta_data[0]['route'] = list()
            self.journey_meta_data[0]['hotel'] = HotelModel()
            self.journey_meta_data[0]['expense'] = list()
            self.journey_meta_data[0]['other'] = list()
            action_types = [('icon detail-journey-label-transport', 10),
                            ('icon detail-journey-label-note', 0),
                            ('icon detail-journey-label-spot', 20),
                            ('icon detail-journey-label-dinner', 21),
                            ('icon detail-journey-label-hotel', 30),
                            ]
            xml_obj = etree.HTML(resp)
            js_data = extract_index_json(resp)

            # 整个journey的行程综述
            route_descs = xml_obj.xpath('//div[@class="J_DetailRouteBrief detail-route-brief"]//p//text()')
            route_descs = map(lambda x: x.strip(), route_descs)
            route_descs = map(lambda x: ':'.join(x), zip(route_descs[0::2], route_descs[1::2]))
            routes = xml_obj.xpath('//div[@class="J_DetailJourney detail-journey detail-journey-4"]/div[position()>2]')
            _hotel = HotelModel()

            if self.temp_type == 'tour':
                for route_index, _route in enumerate(routes):
                    route = RouteModel()
                    head = _route.xpath(('./div[@class="detail-journey-head"]/strong/text() | '
                                         './div[@class="detail-journey-head"]/text()'))
                    head = '\n'.join(head).strip().split('\n')

                    head = filter(lambda x: x, map(lambda x: x.strip(), head))
                    if len(head) <= 2:
                        citys = head[1:]
                    else:
                        citys = head[2:]
                    for city in citys:
                        route.add_city(name=city)
                    desc = '<br>'.join(_route.xpath('./div[@class="detail-journey-desc"]/text()')).strip()
                    route.desc = desc if desc else ' '.join(head)
                    details = _route.xpath('./div[position()>2]')
                    # 节点类型 0:其他 10:交通 11:飞机 20:景点 21:用餐 22:玩乐 23:自由活动 30:酒店
                    for detail in details:

                        detail_info = dict()
                        action_flag = True
                        _title = None
                        _action_type = None
                        for action_type in action_types:
                            _title = detail.xpath('./div[@class="detail-journey-title"]')
                            _type_xpath = './/i[@class="{}"]'.format(action_type[0])
                            _type = detail.xpath(_type_xpath)
                            if len(_type) > 0:
                                _action_type = action_type[1]
                                action_flag = False
                                break
                        if action_flag:
                            _action_type = 0
                        detail_info['type'] = _action_type
                        _img_list = map(lambda x: x.strip(), detail.xpath(('.//img/@data-src')))  # 可能为空
                        try:
                            detail_info['name'] = ''.join(map(lambda x: x.strip().strip(':'),
                                                              _title[0].xpath('./text()|./*//text()')))
                        except Exception as e:
                            detail_info['name'] = ''
                        # journey_desc
                        _desc = detail.xpath('.//div[@class="detail-journey-desc"]/text()')  # 可能为空
                        detail_info['desc'] = _desc[0] if _desc else ''
                        detail_info['image_list'] = _img_list

                        if not (detail_info['desc'] and detail_info['name'] and detail_info['image_list']):
                            continue
                        route.add_detail(detail_info)
                        try:
                            route.desc = route_descs[route_index]
                        except:
                            pass
                        if 30 == _action_type:
                            _hotel.add_plans(dict(name=detail_info['name'].replace('住宿 · ', ''),
                                                  intro=detail_info['desc'],
                                                  img=detail_info['image_list']))
                    if route in self.journey_meta_data[0]['route']:
                        continue
                    self.journey_meta_data[0]['route'].append(route)
            elif self.temp_type == 'product':
                action_types = {'icon detail-journey-label-transport': 10,
                                'icon detail-journey-label-note': 0,
                                'icon detail-journey-label-spot': 20,
                                'icon detail-journey-label-dinner': 21,
                                'icon detail-journey-label-hotel': 30}
                for route_index, _route in enumerate(routes):
                    route = RouteModel()
                    detail_info = dict()
                    head = _route.xpath(('./div[@class="detail-journey-head"]/strong/text() | '
                                         './div[@class="detail-journey-head"]/text()'))
                    head = '\n'.join(head).strip().split('\n')
                    head = filter(lambda x: x, map(lambda x: x.strip(), head))
                    if len(head) <= 2:
                        citys = head[1:]
                    else:
                        citys = head[2:]
                    for city in citys:
                        route.add_city(name=city)
                    title = ''.join(_route.xpath('./div[@class="detail-journey-title"]/text()'))
                    action_type = _route.xpath('./div[@class="detail-journey-title"]/i')
                    if action_type:
                        action_type = _route.xpath('./div[@class="detail-journey-title"]/i/@class')
                        type = action_types[''.join(action_type)]
                        detail_info['name'] = title
                        detail_info['type'] = type
                    else:
                        type = 0
                    desc = '<br>'.join(_route.xpath('./div[@class="detail-journey-desc"]/text()')).strip()
                    _img_list = map(lambda x: x.strip(), _route.xpath(('.//img/@data-src')))  # 可能为空
                    # 节点类型 0:其他 10:交通 11:飞机 20:景点 21:用餐 22:玩乐 23:自由活动 30:酒店
                    detail_info['image_list'] = _img_list
                    detail_info['stime'] = ''
                    detail_info['dur'] = 0
                    detail_info['desc'] = desc

                    route.add_detail(detail_info)
                    route.desc = ' '.join(head)
                    if type and 30 == type:
                        _hotel.add_plans(dict(name=detail_info['name'].replace('住宿 · ', ''),
                                              intro=detail_info['desc'],
                                              img=detail_info['image_list']))
                    self.journey_meta_data[0]['route'].append(route)


            self.journey_meta_data[0]['hotel'] = _hotel

            # tour
            fee_body = xml_obj.xpath(('//div[@class="J_DetailFee section-box detail-upgrade"]/'
                                      'div[@class="section-box-body"]'))
            cost_items = []
            if fee_body:
                fee_content = fee_body[0].xpath('./div')
                for fee_item in zip(fee_content[0::2], fee_content[1::2]):
                    content = ''.join(map(lambda x: x.lstrip(), fee_item[1].xpath('.//*/text()'))).replace('\n', '<br>')
                    if fee_item[0].xpath(u'.//h3[contains(text(),"费用包含")]'):
                        cost_include = {'type': 0, 'title': '费用包含', 'content': content}
                        cost_items.append(cost_include)
                    elif fee_item[0].xpath(u'.//h3[contains(text(),"费用不包含")]'):
                        cost_exclude = {'type': 1, 'title': '费用不包含', 'content': content}
                        cost_items.append(cost_exclude)
            else:
                include_content = re.findall(r'<div.*?class=\"J_pkgInstruction_costContain\".*?>.*?<div.*?class=\"section-box-content\".*?>(.+?)</div>', resp, re.S)
                include_content = ''.join(map(lambda x: x.strip(), include_content))

                # include_content = '<br>'.join(xml_obj.xpath('//div[@class="J_pkgInstruction_costContain"]/div'
                #                                           '[@class="section-box-content"]/text()'))
                cost_include = {'type': 0, 'title': '费用包含', 'content': include_content}
                exclude_content = re.findall(r'<div.*?class=\"J_pkgInstruction_costNoContain\".*?>.*?<div.*?class=\"section-box-content\".*?>(.+?)</div>', resp, re.S)
                exclude_content = ''.join(map(lambda x: x.strip(), exclude_content))
                # exclude_content = '<br>'.join(xml_obj.xpath('//div[@class="J_pkgInstruction_costNoContain"]/div'
                #                                           '[@class="section-box-content"]/text()'))
                cost_exclude = {'type': 1, 'title': '费用不包含', 'content': exclude_content}
                cost_items.append(cost_include)
                cost_items.append(cost_exclude)

            self.journey_meta_data[0]['expense'] = cost_items

            # policy_content = xml_obj.xpath(('//div[@class="J_DetailPolicy section-box detail-policy"]/'
            #                                 'div[@class="section-box-body"]//*/text() | //div'
            #                                 '[@class="J_pkgInstruction_reserveNotice"]/div'
            #                                 '[@class="section-box-content"]/text()'))
            policy_content = xml_obj.xpath(('//div[@class="J_DetailPolicy section-box detail-policy"]/'
                                            'div[@class="section-box-body"]//*/text()'))
            if not policy_content:
                policy_content = re.findall(r'<div.*?class=\"J_pkgInstruction_reserveNotice\".*?>.*?<div.*?class=\"section-box-content\".*?>(.+?)</div>', resp, re.S)
                pre_info = ''.join(map(lambda x: x.strip(), policy_content))
                pre_info = ''.join(map(lambda x: x.lstrip(), policy_content)).replace('\n', '<br>')
            else:
                pre_info = ''.join(map(lambda x: x.lstrip(), policy_content)).replace('\n', '<br>')
            # pre_info = self.delete_space(policy_content)
            self.journey_meta_data[0]['other'].append({'title': 'pre_info', 'content': pre_info.replace('•', '<br>•', 1)})

        def parse_extra_jouney(req, resp):
            # 节点类型 0:其他 10:交通 11:飞机 20:景点 21:用餐 22:玩乐 23:自由活动 30:酒店
            code_map = {'1': 20, '2': 30, '3': 10, '4': 21}
            if 0 != resp.get('code'):
                raise Exception
            journey_index = req['field_need']['index']
            self.journey_meta_data[journey_index]['route'] = list()
            self.journey_meta_data[journey_index]['hotel'] = HotelModel()
            self.journey_meta_data[journey_index]['expense'] = list()
            self.journey_meta_data[journey_index]['other'] = list()
            assert isinstance(resp['data'], dict)
            journey_detail = resp['data'].get('journeyDetail')
            if isinstance(journey_detail, list):
                """只有简要的行程信息"""
                for _route in journey_detail:
                    route = RouteModel()
                    _title = _route.get('title', '')
                    _subtitle = _route.get('subTitle', '')
                    route.desc = _title + _subtitle
                    route.add_city(name=_subtitle)
                    if '自由活动' == _subtitle:
                        _type = 23
                    elif _route.get('pojName'):
                        _type = 20
                    elif '航班' in _subtitle:
                        _type = 10
                    else:
                        _type = 0

                    one_detail = {
                        'type': _type,
                        'name': _subtitle,
                        'stime': '',
                        'dur': 0.0,
                        'desc': _route.get('content', ''),
                        'image_list': map(lambda x: x['imgUrl'], _route['images'])
                    }

                    route.add_detail(one_detail)
                    self.journey_meta_data[journey_index]['route'].append(route)

            elif isinstance(journey_detail, dict):
                """与HTML解析的第一行程拥有>=的信息量"""
                cost_include = journey_detail.get('costInclude', [])

                include_con = ''
                for cost in cost_include:
                    include_con += cost['title'] + '\n' + '\n'.join(cost['content']) + '\n'

                self.journey_meta_data[journey_index]['expense'].append({'type': 0, 'title': '费用包含',
                                                                         'content': include_con.strip()})
                cost_exclude = journey_detail.get('costExclude', [])
                exclude_con = ''
                for cost in cost_exclude:
                    exclude_con += cost['title'] + '\n' + '\n'.join(cost['content']) + '\n'
                self.journey_meta_data[journey_index]['expense'].append({'type': 1, 'title': '费用不包含',
                                                                         'content': exclude_con.strip()})
                book_info = journey_detail.get('bookNotice')
                book_con = ''
                for book in book_info:
                    book_con += book['title'] + '\n' + '\n'.join(book['content']) + '\n'
                self.journey_meta_data[journey_index]['other'].append({'title': 'pre_info',
                                                                       'content': book_con})
                routes = journey_detail['journeyFourDetail']['detail']
                routes_view = journey_detail['journeyFourDetail']['overview']
                _hotel = HotelModel()
                for route_index, _route in enumerate(routes):
                    route = RouteModel()
                    route_data = _route['data']
                    for detail in route_data:
                        city_name = detail.get('to')
                        title = detail.get('title', '')
                        if city_name:
                            title = '-'.join([detail.get('from', ''), detail.get('to', '')])
                            city_id = detail.get('toId', '')
                            route.add_city(city_id, city_name)
                        code_type = code_map.get(str(detail.get('moduleTypeValue', '0')), 0)

                        img_list = detail.get('picture')
                        img_list = img_list if img_list else []
                        poi = detail.get('poiDescription')
                        poi = poi if poi else ''
                        content = detail.get('content')
                        content = content if content else ''
                        remark = detail.get('remark')
                        remark = remark if remark else ''
                        inner_data = detail.get('data', [])
                        address = detail.get('address')
                        address = address if address else ''
                        if inner_data:
                            title = inner_data[0].get('title', '')
                            address = inner_data[0].get('address', '')
                            address = address if address else ''
                            p = inner_data[0].get('poiDescription', '')
                            poi += p if p else ''
                            content += inner_data[0].get('content', '')
                            remark += inner_data[0].get('remark', '')
                            img_list.extend(inner_data[0].get('picture', []))
                        img_list = map(lambda img: img['url'], img_list)
                        title = tools.unescape(tools.remove_html_tags(title))
                        poi = tools.unescape(tools.remove_html_tags(poi))
                        content = tools.unescape(tools.remove_html_tags(content))
                        remark = tools.unescape(tools.remove_html_tags(remark))

                        if 30 == int(code_type):  # 酒店
                            one_hotel = {
                                'name': title,
                                'intro': '\n'.join([poi, content, remark]),
                                'img': img_list,
                                'addr': address
                            }
                            _hotel.add_plans(one_hotel)
                        elif 21 == int(code_type):  # 用餐
                            title = '-'.join([poi, content, remark])
                            content = '\n'.join([content, remark])
                        one_detail = {
                            'type': code_type,
                            'name': title,
                            'stime': '',
                            'dur': 0.0,
                            'desc': '\n'.join([poi, content, remark]),
                            'image_list': img_list
                        }
                        view = routes_view[route_index]
                        route.desc = ':'.join([view.get('journeyName', ''), view.get('journeyDescription', '')])
                        route.add_detail(one_detail)
                        if route in self.journey_meta_data[journey_index]['route']:
                            continue
                        self.journey_meta_data[journey_index]['route'].append(route)
                self.journey_meta_data[journey_index]['hotel'] = _hotel

        parser_map = {
            '1': parse_first_journey,
            '2': parse_extra_jouney
        }
        index_key = '2' if isinstance(resp, dict) else '1'
        parser_map[index_key](req, resp)

    def parse_supplier(self, req, resp):
        """解析供应商信息列表"""

        if 0 != resp.get('code'):
            raise Exception
        suppliers = resp['data']['supplier'].get('rows', [])
        _suppliers = dict()
        for supplier in suppliers:
            _suppliers[supplier['resId']] = {'brand': supplier['companyName'],
                                             'supplier': supplier['fullName']}
        for i in range(len(self.journey_meta_data)):
            resid = self.journey_meta_data[i].get('resid', '')
            try:
                self.journey_meta_data[i]['supplier'] = _suppliers[resid]['supplier']
                self.journey_meta_data[i]['brand'] = _suppliers[resid]['brand']
            except:
                self.journey_meta_data[i]['supplier'] = ''
                self.journey_meta_data[i]['brand'] = ''
                continue

    def parse_visa(self, req, resp):
        visa_blank = {'title': 'visa_info', 'content': ''}
        if 0 != resp.get('code'):
            self.pub_meta['visa'] = visa_blank
            return
        data = resp.get('data')
        if not data or not isinstance(data, list):
            self.pub_meta['visa'] = visa_blank
        visa_data = data[0]
        name = tools.unescape(tools.remove_html_tags(visa_data['visaInfo']['name']))
        notice = tools.unescape(tools.remove_html_tags(visa_data['visaInfo']['bookNotice']))
        remark = tools.unescape(tools.remove_html_tags(visa_data['visaInfo']['custRemark']))
        materials = tools.unescape(
            tools.remove_html_tags('\n'.join([m['materialDesc'] for m in visa_data['visaMaterial']])))
        visa_content = '{}\n注意事项:\n{}\n提醒:\n{}\n材料:\n{}'.format(name, notice, remark, materials)
        visa_blank['content'] = visa_content
        self.pub_meta['visa'] = visa_blank


    def parse_vacation(self, req, resp):
        """最终汇总组装"""

        def combine_tour_list(meta):
            child_tour = TourModel()
            child_tour.name = '儿童'
            child_tour.price = meta['child_price']
            child_tour.rest = meta['child_rest']
            child_tour.age_lower = 2
            child_tour.age_upper = 11

            adult_tour = TourModel()
            adult_tour.name = '成人'
            adult_tour.price = meta['adult_price']
            adult_tour.rest = meta['adult_rest']
            adult_tour.age_lower = 12
            adult_tour.age_upper = 0
            return [adult_tour, child_tour]

        result = list()
        for journey in self.journey_meta_data:
            cals = journey['suit_date']
            if not cals:
                continue
            for cal in cals.values():
                if not journey.get('route') or not cal:
                    continue
                vacation = VacationModel()
                vacation.name = self.pub_meta['name']
                vacation.pid_3rd = self._task['id']  # vacation.product_id = self._task['id']
                vacation.sid = journey['supplier'] #vacation.supplier = journey['supplier']
                # vacation.brand = journey['brand']
                date_nouse = cal['date']
                vacation.date = str(date_nouse).replace('-', '') #vacation.start_date = cal['date']
                vacation.dest = [{"id": self.task.ticket_info['vacation_info']['search_dest_city_id'],
                                  "name": self.task.ticket_info['vacation_info']['search_dest_city'],
                                  "mode": 1}]
                vacation.dept = [{"id": "", "name": self.task.ticket_info['vacation_info']['dept_city']}]
                if self.pub_meta['team_city_name']:
                    vacation.dept_city = [{'id': '',
                                           'name': self.pub_meta['team_city_name']}]
                else:
                    vacation.dept_city = []
                vacation.set_name = journey['name']
                if self.temp_type == 'product':
                    vacation.set_name = '无'
                vacation.set_id = str(journey['id'])
                vacation.star_level = self.pub_meta['star_level']
                vacation.time = len(journey['route'])    #vacation.num_of_days = len(journey['route'])
                vacation.highlight = self.pub_meta['highlight']
                dead = datetime.strptime(date_nouse, '%Y-%m-%d') - timedelta(days=int(vacation.book_pre))
                vacation.sell_date_late = dead.strftime('%Y%m%d')  #vacation.sell_deadline = dead.strftime('%Y-%m-%d')
                vacation.book_pre = cal['book_pre']
                vacation.image_list = self.pub_meta['img_list']
                vacation.rec = self.pub_meta['recommend']
                vacation.single_room = cal['room_fee']
                vacation.route_day = journey['route']
                expense = copy.deepcopy(journey['expense']) if journey['expense'] else copy.deepcopy(
                    self.journey_meta_data[0]['expense'])
                vacation.expense = expense
                vacation.hotel = journey['hotel']
                other = copy.deepcopy(journey.get('other')) if journey.get('other') else copy.deepcopy(
                    self.journey_meta_data[0]['other'])
                vacation.other = other
                vacation.add_other(self.pub_meta.get('visa', {'title': 'visa_info', 'content': ''}))
                vacation.tourist = combine_tour_list(cal)
                vacation.pid = "gty" + datetime.now().strftime('%Y-%m-%d') + '%s' % int(time.time() * 100)
                vacation.extra_traffic = self.extra_traffic
                vacation.extra_city = self.extra_city
                vacation.multi_city = self.multi_city
                vacation.is_multi_city = self.is_multi_city
                vacation.ctime = int(time.time())
                vacation.first_image = self._task['first_image']
                try:
                    text = expense[0].get('content', '')
                    vacation.child_standard = ''.join(re.findall(ur'儿童价标准：(.+)', text, re.S)).replace('<br>', '').strip()
                except:
                    vacation.child_standard = ''
                # vacation.url = self.task.ticket_info['vacation_info']['url']
                # vacation.ccy = self.ccy
                # vacation.stat = self.stat
                # vacation.disable = self.disable

                result.append(vacation.to_dict())
        return result


if __name__ == "__main__":

    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    task = Task()
    task.ticket_info['vacation_info'] = {'search_dept_city_id': '1602', 'url': 'http://www.tuniu.com/tour/210140910', 'brand': '罗马假期', 'dept_city': '南京', 'search_dest_city': '普吉岛', 'first_image': 'http://m.tuniucdn.com/fb2/t1/G5/M00/09/0D/Cii-tFomThiIDU_GAAEyLjwgIi4AAAb6QIwFvUAATJG78_w160_h90_c1_t0.jpeg', 'search_dept_city': '南京', 'search_dest_city_id': '', 'id': '210140910'}
    spider = TuniuVacationSpider()
    print '------'
    spider.task =task
    
    code = spider.crawl()
    result = spider.result
    import pprint
    pprint.pprint(result['vacation'])

    print code
