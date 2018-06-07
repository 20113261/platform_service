#!/usr/bin/env python
# -*- coding:utf-8 -*-

from mioji.common.spider import Spider,request
import execjs
import re
from mioji.common.spider import PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
from mioji.common import parser_except
import os
from toolbox import Common
from lxml import html
import traceback
import json
from copy import deepcopy
import mioji
mioji.common.spider.NEED_FLIP_LIMIT = False
mioji.common.spider.MAX_FLIP = 300
source_map = {
    'agoda': 'agoda',
    'ctripintdaodao': 'ctrip',
    'bookingcn': 'booking',
    'hotelscom2': 'hotels',
    'elongintdaodaob2v': 'elong',
    'ctripdaodao': 'ctrip',
    'elongdaodao': 'elong'

}
sources = ['agoda','booking','ctrip','elong','expedia','hotels']
current_path = os.path.abspath(os.path.dirname(__file__))
path = '/'.join([current_path,'decode_node.js'])
with open(path) as f:
    js_str = f.read()
phantomjs = execjs.get('PhantomJS')
base_url = 'https://www.tripadvisor.cn'

class CrawlHotelUrl(Spider):

    source_type = "daodaoListHotel"
    targets = {
        'hotel': {},
        # 'travelzoolist': {}
    }
    old_spider_tag = {
        'daodaoListHotel': {'required': 'hotel'}
    }
    def __init__(self):
        super(CrawlHotelUrl, self).__init__()

    def targets_request(self):
        @request(retry_count=5, async=True, proxy_type=PROXY_REQ)
        def first_req():

            url = self.task.ticket_info['url']
            return {
                'req':{'url': url, 'method': 'get'},
                'data':{'content_type': 'html'},
                'user_handler': [self.get_max_page, self.get_location_position]
            }

        yield first_req

        @request(retry_count=10, proxy_type=PROXY_FLLOW)
        def second_req():
            headers = {
                # 'Host': 'cc.ddcdn.com',
                'Origin': 'https://www.tripadvisor.cn',
            }
            max_page = self.user_datas['max_page']
            saves = []
            for page in xrange(1, max_page):
                url = self.task.ticket_info['url']
                url_list = url.split('-')
                referer_list = deepcopy(url_list)
                number = page*30
                insert_str = "oa{0}".format(number)
                referer_str = "oa{0}".format(number-30)
                url_list.insert(2, insert_str)
                referer_list.insert(2, referer_str)
                url = '-'.join(url_list)
                referer = '-'.join(referer_list)
                headers['Referer'] = url if page == 1 else referer
                saves.append(
                    {
                        'req': {'url':  url, 'method': 'get', 'header': headers, 'cookies': self.cookies},
                        'data': {'content_type': 'html'},
                        'user_handler': [self.get_location_position]
                    }
                )
            return saves

        yield second_req

        @request(retry_count=10, proxy_type=PROXY_FLLOW, binding=['hotel',])
        def three_req():
            need_req = self.user_datas['need_req']
            result = []
            for hotel_name, hotel_name_en, url in need_req:
                print hotel_name, hotel_name_en, url
                result.append({
                    'req': {'url': url, 'method': 'get'},
                    'data': {'content_type': 'html'},
                    'hotel_name':hotel_name,
                    'hotel_name_en': hotel_name_en
                })
            return result
        yield three_req

        # @request(retry_count=10, proxy_type=PROXY_REQ, binding=['hotel', ])
        # def four_req():
        #     hotels = self.result['travelzoolist']
        #     saves = []
        #     for seq, hotel in enumerate(hotels):
        #         hotel_urls = hotel.get('hotels', {})
        #         hotel_name_en = hotel['hotel_name_en']
        #         hotel_name = hotel['hotel_name']
        #         for key, url in hotel_urls.items():
        #             if url is None:continue
        #             print seq, key, url
        #             if key in sources:
        #             # if key in ['HotelsCom2', 'HostelWorld', 'Agoda', 'Hyatt_Derbysoft', 'HotelQuickly', 'CTripINTDaoDao', 'ELongINTDaoDaoB2V', 'IHG', 'BookingCN']:
        #                 url = url.replace('www.tripadvisor.cn', 'www.tripadvisor.com')
        #                 saves.append(
        #                     {
        #                         'req': {'url': url, 'method': 'get'},
        #                         'data': {'content_type': 'string'},
        #                         # 'source': source_map[key],
        #                         'source': key,
        #                         'url': url,
        #                         'index': seq,
        #                         # 'hotel_name': hotel_name,
        #                         # 'hotel_name_en': hotel_name_en
        #                     }
        #                 )
        #     return saves
        #
        # yield four_req

    def join_secrt_url(self, secrt):
        source_url = phantomjs.compile(js_str).call('decode', secrt)
        url = ''.join([base_url, source_url])
        return url

    def get_max_page(self, req, data):
        root = data
        a_tag = root.xpath('//a[contains(@class,"pageNum last")]/text()')
        max_page = 1
        if a_tag:
            max_page = int(a_tag[0])
        self.user_datas['max_page'] = max_page
        self.cookies = req['resp'].cookies

    def get_location_position(self, req, data):
        root = data
        # div_list = root.xpath('//div[@id="taplc_hsx_hotel_list_lite_dusty_hotels_combined_sponsored_0"]/div/div[@class="prw_rup prw_meta_hsx_responsive_listing bottom-sep"]')
        div_list = root.xpath('.//div[contains(@class,"meta_listing ui_columns")]')
        for div in div_list:
            localtion_id = div.attrib.get('data-locationid')
            assert localtion_id, 'localtion_id 不可为空'
            try:
                temp_name = div.xpath('.//div[@class="listing_title"]/a/text()')[0]
            except:
                temp_name = div.xpath('./div//div[contains(@class,"listing_title")]/div/a/text()')[0]
            print temp_name
            judge = Common.has_any(temp_name, Common.is_chinese)
            if judge:
                hotel_name = temp_name
                hotel_name_en = ''
            else:
                hotel_name = ''
                hotel_name_en = temp_name

            more = div.xpath('.//div[@class="view_all is-shown-at-tablet"]')
            if more:
                url = 'https://www.tripadvisor.cn/OverlayWidgetAjax?Mode=HOTELS_VIEW_ALL_OFFERS&metaReferer=Hotels&listPos={0}&locationId={1}&ttPlc=Hotels_MainList'
                location_id = div.attrib.get('data-locationid')
                position = div.attrib.get('data-index')
                url = url.format(str(position).strip(),str(location_id).strip())
                self.user_datas['need_req'].append((hotel_name, hotel_name_en, url))
            else:
                values = {}
                # first = div.xpath('.//div[@class="premium_offer no_cpu ui_columns is-mobile is-gapless is-multiline withXthrough metaOffer"]')[0]
                try:
                    first = div.xpath('.//div[contains(@class, "premium_offer no_cpu ui_columns is-mobile is-gapless is-multiline")]')[0]
                    source = first.attrib.get('data-provider')
                    real_source = source_map.get(source.lower(), source)
                    secrt = first.attrib.get('data-clicktoken')
                    url = self.join_secrt_url(secrt) if secrt else secrt
                    values[real_source] = url
                except IndexError as e:
                    # print traceback.format_exc(e)
                    pass

                others = div.xpath('.//div[@class="text-links is-shown-at-tablet"]/div')
                for other in others:
                    source = other.attrib.get('data-provider')
                    real_source = source_map.get(source.lower(), source)
                    secrt = other.attrib.get('data-clicktoken')
                    url = self.join_secrt_url(secrt) if secrt else secrt
                    values[real_source] = url

                self.result['hotel'].append({'hotel_name': hotel_name, 'hotel_name_en': hotel_name_en, 'hotels': values, 'localtion_id': localtion_id})

    def parse_hotel(self, req, data):
        # print req['resp'].content
        hotel_name = req['hotel_name']
        hotel_name_en = req['hotel_name_en']
        root = data
        result = {}
        # base_url = 'https://www.tripadvisor.cn'
        # judge = Common.has_any(hotel_name,Common.is_chinese)
        # if judge:
        #     result['hotel_name'] = hotel_name
        # else:
        #     result['hotel_name_en'] = hotel_name

        result['hotel_name'] = hotel_name
        result['hotel_name_en'] = hotel_name_en
        div_list = root.xpath('//div/div')
        localtion_id = None
        values = {}
        for div in div_list:
            source = div.attrib.get('data-provider','').strip()
            data_locationId = div.attrib.get('data-locationid', '').strip()
            localtion_id = data_locationId
            real_source = source_map.get(source.lower(), source)
            # results['real_source'] = source
            # if source_map.get(source):
            #     source = source_map[source]
            token_str = div.attrib.get('data-clicktoken','')
            if not token_str:
                continue
            url = phantomjs.compile(js_str).call('decode', token_str)
            source_url = url
            url = ''.join([base_url,source_url])
            values[real_source] = url
        assert localtion_id, 'localtion_id 不可为空'
        result['localtion_id'] = localtion_id
        result['hotels'] = values
        return result

    # def parse_hotel(self, req, resp):
    #     source = req['source']
    #     url = req['url']
    #     index = req['index']
    #     # hotel_name = req['hotel_name']
    #     # hotel_name_en = req['hotel_name_en']
    #
    #     real_url = None
    #     print source, url
    #     try:
    #         if source == 'agoda':
    #         # if source in ('Agoda'):
    #             agoda_json = re.search(r'window.searchBoxReact = (.*)(?=;)', resp).group(1)
    #             agoda_json = json.loads(agoda_json)
    #             url = agoda_json.get('recentSearches', [])[0].get('data', {}).get('url')
    #             base_url = 'https://www.agoda.com'
    #             real_url = ''.join([base_url, url])
    #         elif source == 'booking':
    #         # elif source in ('BookingCN'):
    #             root = html.fromstring(resp)
    #             real_url = root.xpath('//link[@rel="canonical"]/@href')[0]
    #         elif source == 'ctrip':
    #         # elif source in ('CTripINTDaoDao'):
    #             ctrip_json = re.search(r'hotelPositionJSON: (.*)(?=,)', resp).group(1)
    #             ctrip_json = json.loads(ctrip_json)
    #             url = ctrip_json[0].get('url')
    #             base_url = "http://hotels.ctrip.com"
    #             real_url = ''.join([base_url, url])
    #         elif source == 'elong':
    #         # elif source in ('ELongINTDaoDaoB2V'):
    #             hotel_id = re.search(r'hotelId":"([0-9]+)"', resp).group(1)
    #             real_url = 'http://ihotel.elong.com/{0}/'.format(hotel_id)
    #         elif source == 'expedia':
    #             real_url = None
    #         elif source == 'hotels':
    #         # elif source in ('HotelsCom2'):
    #             root = html.fromstring(resp)
    #             hotel_id = root.xpath('//div[@id="listings"]//li')[0].attrib.get('data-hotel-id')
    #             real_url = "https://ssl.hotels.cn/ho{0}/?pa=1&q-check-out=2018-04-16&tab=description&q-room-0-adults=2&YGF=7&q-check-in=2018-04-15&MGT=1&WOE=1&WOD=7&ZSX=0&SYE=3&q-room-0-children=0".format(hotel_id)
    #     except (IndexError, TypeError, AttributeError) as e:
    #         print traceback.format_exc(e)
    #         raise parser_except.ParserException(22, '重试一波')
    #         real_url = None
    #
    #     temp_hotel = self.result['travelzoolist'][index].copy()
    #     temp_hotel['hotels'][source] = real_url
    #
    #     return temp_hotel


if __name__ == "__main__":

    from mioji.common import spider
    from mioji.common.utils import simple_get_proxy, simple_get_http_proxy
    # spider.slave_get_proxy = simple_get_proxy
    spider.slave_get_proxy = simple_get_http_proxy
    crawl = CrawlHotelUrl()
    task = Task()
    # task.ticket_info['url'] = 'https://www.tripadvisor.cn/Hotels-g28970-Washington_DC_District_of_Columbia-Hotels.html'
    # task.ticket_info['url'] = 'https://www.tripadvisor.cn/Hotels-g297517-oa60-Dili_Dili_District-Hotels.html'
    task.ticket_info['url'] = 'https://www.tripadvisor.cn/Hotels-g293938-Bandar_Seri_Begawan_Brunei_Muara_District-Hotels.html'
    crawl.task = task
    crawl.crawl()
    # print json.dumps(crawl.result['travelzoolist'], ensure_ascii=False)
    print json.dumps(crawl.result['hotel'], ensure_ascii=False)



