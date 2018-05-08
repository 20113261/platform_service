#!/usr/bin/env python
# -*- coding:utf-8 -*-

from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
from mioji.common.utils import simple_get_socks_proxy
from lxml.html import tostring
import traceback
from requests import ConnectionError, ConnectTimeout
import json
from mioji.common import parser_except
source_map = {
    'booking.com': 'booking',
    'hotels.com': 'hotels',
    'expedia.cn': 'expedia',
    'agoda': 'agoda',
    'expedia.com.vn': 'expedia',
    'expedia.com.tw': 'expedia',

}
mysources = set(source_map.values())

class GoogleListSpider(Spider):

    source_type = 'googleListHotel'

    targets = {
        'hotel': {}
    }
    old_spider_tag = {
        'googleListHotel': {'required': 'hotel'}
    }

    def __init__(self):
        super(GoogleListSpider, self).__init__()

    def targets_request(self):
        @request(retry_count=10, async=True, proxy_type=PROXY_REQ)
        def keyword_search():
            hotel_name = self.task.ticket_info['hotel_name'].replace(' ','+')
            return {
                    'req': {
                            'url': 'https://www.google.com.hk/search?&q=' + hotel_name + '&oq=' + hotel_name,
                            'method': 'get',
                            'timeout': 5000
                            },
                    'data': {'content_type': 'html'},
                    'user_handler':[self.get_search_result]
                    }
        yield keyword_search

        if self.user_datas['search_result'].get('expedia',''):
            @request(retry_count=10, proxy_type=PROXY_REQ, async=True)
            def change_expedia_url():
                expedia_url = self.user_datas['search_result'].get('expedia','')
                if expedia_url:
                    return {
                        'req': {'url':expedia_url,'method': 'get'},
                        'data': {'content_type': 'html'},
                        'user_handler': [self.get_change_result]
                    }
            yield change_expedia_url

        @request(retry_count=10, proxy_type=PROXY_REQ, user_retry=True, binding=['hotel'])
        def get_source_url():
            sources = self.user_datas['search_result']
            if sources:
                save_result = []
                for source,value in sources.items():
                    if source not in mysources:continue
                    if source == 'expedia':
                        url = 'https://www.expedia.com.vn/Hotel-Search-Data?'
                        save_result.append(
                            {
                                'req':{'url':url,'data':value,'method':'post', 'timeout': 5000},
                                'data': {'content_type':'string'},
                                'source': source
                            }
                        )
                    else:
                        save_result.append(
                            {
                                'req':{'url':value,'method':'get', 'timeout': 5000},
                                'data':{'content_type':'html'},
                                'source': source
                            }
                        )
                return save_result
        yield get_source_url

    def user_retry_err_or_resp(self, err_or_resp, retry_count, request_template, is_exc):
        print '8'*100

    def get_search_result(self,req,data):
        root = data
        results = root.xpath('//div[contains(@class,"lhpr-content-item")]')
        temp_save = {}
        for result in results[:-1]:
            url = result.xpath('div/a/@href')[0]
            source = result.xpath('div/a/img/@alt')[0].strip().lower()
            if source_map.get(source):
                source = source_map.get(source)
            temp_save[source] = url
        if not temp_save:
           raise parser_except.ParserException(29, "谷歌侧边无酒店")

            #raise parser_except.ParserException(29, "谷歌侧边无酒店")
            #print source, url
        #print 'temp',temp_save
        self.user_datas['search_result'] = temp_save

    def get_change_result(self,req,data):
        url = req['resp'].url
        res = url.split('&')
        temp_dic = {}
        temp_dic['responsive'] = 'true'
        temp_dic['hsrIdentifier'] = 'HSR'
        temp_dic[res[0].split('?')[1].split('=')[0].encode('utf-8')] = res[0].split('?')[1].split('=')[1].encode(
            'utf-8')
        for i in res[1:]:
            temp_dic[i.split('=')[0].encode('utf-8')] = i.split('=')[1].encode('utf-8')
        self.user_datas['search_result']['expedia'] = temp_dic

    def parse_hotel(self,req,data):
        root = data
        source = req['source']
        temp_save = {}
        try:
            if source == 'agoda':
                agoda_url = root.xpath('/html/head/meta[10]/@content')[0]
                temp_save['agoda'] = agoda_url.replace('/vi-vn/', '/zh-cn/')
            elif source == 'booking':
                if root.xpath('//*[@id="hotellist_inner"]/div[1]/div[2]/div[1]/div[1]/h3/a/@href'):
                    booking_url = 'https://www.booking.com' + \
                              root.xpath('//*[@id="hotellist_inner"]/div[1]/div[2]/div[1]/div[1]/h3/a/@href')[0]
                else:
                    booking_url = 'https://www.booking.com' + \
                                  root.xpath('//*[@id="hotellist_inner"]/div[1]/div[3]/div[1]/div[1]/h3/a/@href')[0]
                booking_url = booking_url.replace('\n', '').replace('.vi.html', '.zh-cn.html')
                temp_save[source] = booking_url
            elif source == 'hotels':
                hotels_url = 'https://zh.hotels.com' + root.xpath('//*[@id="listings"]/ol/li[1]/article/div/div[1]/h3/a/@href')[0]
                temp_save[source] = hotels_url
            elif source == 'expedia':
                data = json.loads(root)
                ep_url = data['searchResults']['retailHotelModels'][0]['infositeUrl']
                temp_save['expedia'] = ep_url
        except IndexError as e:
            print traceback.format_exc(e)
            raise parser_except.ParserException(22, '重试一波')
        return temp_save

if __name__ == "__main__":
    from mioji.common.utils import simple_get_proxy
    from mioji.common import spider
    spider.slave_get_proxy = simple_get_proxy
    googlespider = GoogleListSpider()
    task = Task()
    task.ticket_info['hotel_name'] = "Parkroyal Parramatta"
    # task.ticket_info['hotel_name'] = "卡尔玛旅馆Pension La Calma"
    # task.ticket_info['hotel_name'] = "Pension La Calma"
    task.ticket_info['hid'] = 1
    googlespider.task = task
    googlespider.crawl()
    print googlespider.result['hotel']
    #print 'cs_',crawl.result,type(crawl.result)
