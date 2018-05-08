#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17/2/15 下午3:04
# @Author  : sws
# @Site    : 抓取agoda网站上的所有的城市
# @File    : source_city_name.py
# @Software: PyCharm

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

from lxml import html as HTML, etree
import re
import json
from mioji.common import spider
spider.MAX_FLIP=5000
from mioji.common.task_info import Task
from mioji.common.spider import Spider, request, PROXY_REQ
import requests
# from mioji.common.parser_except import ParserException, TASK_ERROR
F_URL = 'https://www.agoda.com/zh-cn/world.html'

'''
1从 https://www.agoda.com/zh-cn/world.html?ckuid=879e1366-4b50-41db-99ab-9fa01cddee27 获取所有的国家 每个国家的URL形似 https://www.agoda.com/zh-cn/country/south-korea.html?asq=jGXBHFvRg5Z51Emf%2FbXG4w%3D%3D 去掉?后面的一堆东西就可以获取到城市数据了。
2 从 https://www.agoda.com/zh-cn/country/south-korea.html 中获取所有的一级城市网址 类似https://www.agoda.com/zh-cn/city/gangwon-do-kr.html?asq=hG2DT5yaDw2osrn8Q7J0pzlofCSExjkcqHYmDGUNHzaTdvoi8Xcl5weFeG7C6X0hR5e0ZUcVPv8lKz0JCdptdA%3d%3d 去掉?后面的 https://www.agoda.com/zh-cn/city/gangwon-do-kr.html
3 请求2后面的网址 https://www.agoda.com/zh-cn/city/gangwon-do-kr.html
4 根据3返回的页面 获取全部的城市。

新流程：
2.通过国家url请求的到的html中获取https://www.agoda.com/api/zh-cn/GeoApi/...的是api参数，通过该URL请求获取国家区域json数据
3.同样通过区域url获取城市api接口，通过api请求获取该区域的城市数据
'''


class CityList(Spider):
    __type = 'cityList'
    # 基础数据城市酒店列表 & 例行城市酒店
    __targets_version = {
        'cityList_city': {},
    }

    __targets = __targets_version.keys()
    # 关联原爬虫
    #   对应多个原爬虫
    __old_spider_tag = {}

    def __init__(self,*args):
        self.source_type = 'agoda'
        self.targets = {'country':{}}
        super(CityList,self).__init__(*args)
    def old_spider_tag(self):
        return CityList.__old_spider_tag

    def crawl_type(self):
        return CityList.__type

    def targets_parser(self):
        return CityList.__targets

    def parser_targets_version(self):
        return CityList.__targets_version

    def cache_check(self, req, data):
        return False

    def targets_request(self):
        self.user_datas['country_list'] = []
        self.user_datas['state_api'] = []
        self.user_datas['region_dict'] = {}
        self.user_datas['city_dict'] = {}
        
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_country():
            return {
                'req':{'url':F_URL},
                'data': {'content_type': 'string'},
                'user_handler':[self.parse_country],
               }

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True)
        def get_all_states_url():
            country_list = self.user_datas['country_list']

            region_list = []
            for co in country_list:
                region_list.append(
                    {
                        'req':{'url':co[1]},
                        'data': {'content_type': 'string'},
                        'other_info':{'country_name':co[0]},
                        'user_handler':[self.parse_allstate_url],
                    }
                )
            return region_list

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True)
        def get_region():
            states_api_url = self.user_datas['state_api']
            region_list = []
            for co in states_api_url:
                region_list.append(
                    {
                        'req': {'url': co[1]},
                        'data': {'content_type': 'json'},
                        'other_info': {'country_name': co[0]},
                        'user_handler': [self.parse_region],
                    }
                )
            return region_list



        @request(retry_count=3, proxy_type=PROXY_REQ, async=True)
        def get_city():
            import json
            region_dict = json.load(fp=open('region_dict.json','r'))
            city_list = []

            for country in region_dict:
                self.user_datas['city_dict'][country] = {}
                for reg in region_dict[country]:
                    city_list.append(
                        {
                            'req':{'url':reg[1]},
                            'data':{'content_type':'json'},
                            'other_info':{'country_name':country, 'region_name':reg[0]},
                            'user_handler': [self.parse_cityList_city]
                        }
                    )
            return city_list
        return [get_city]

    def parse_country(self, req, data):
        '''
            解析国家
        :return:
        '''
        data = re.sub(r'<input.*?/>', '', data)
        tree = etree.HTML(data)
        ctry_list = []
        a_list = tree.xpath('//li[@data-selenium="country-item"]/a')
        print len(a_list)
        for a in a_list:
            country_name = a.xpath('./text()')[0]
            cou_url = 'https://www.agoda.com' + a.xpath('./@href')[0].split('?')[0]

            ctry_list.append((country_name, cou_url))
        self.user_datas['country_list'] += ctry_list


    def parse_allstate_url(self, req, data):
        '''
            解析区域
        :param req:
        :param data:
        :return:
        '''
        country_code = data.find('AllStates')
        state_api = 'https://www.agoda.com/api/zh-cn/GeoApi/'+data[country_code:country_code+20].strip(',\'\r\n ')
        #tree = HTML.fromstring(data)
        country_name = req['other_info']['country_name']

        self.user_datas['state_api'] += [(country_name,state_api)]

    def parse_region(self,req,data):
        region_list = []
        for per_region in data:
            region_url = 'https://www.agoda.com'+per_region['url']
            state_con = requests.get(region_url).content
            state_code =state_con.find('NeighborHoods')
            city_api = 'https://www.agoda.com/api/zh-cn/GeoApi/'+ state_con[state_code:state_code+20].strip(',\'\r\n ')
            region_name = per_region['name']
            region_list.append((region_name, city_api))

        country_name = req['other_info']['country_name']
        self.user_datas['city_dict'][country_name] = region_list

#         #a_list = tree.xpath('//li[@class="sprite"]/a')
#         a_list = tree.xpath('//a[@data-selenium="city-link"]')
#         print 'len', len(a_list)
#         import gevent
# #         gevent.sleep(3)
#         for a in a_list:
#             region_url = 'https://www.agoda.com' + a.xpath('./@href')[0].split('?')[0]
#             country_name = country_name
#             print region_url
#             region_list.append((country_name, region_url))
#
#         self.user_datas['region_list'] += region_list

    def parse_cityList_city(self, req, data):
        city_list = []
        for per_city in data:
            city_url = 'https://www.agoda.com'+per_city['url']
            city_name = per_city['name']
            city_list.append((city_name, city_url))

        country_name = req['other_info']['country_name']
        region_name = req['other_info']['region_name']
        self.user_datas['city_dict'][country_name][region_name] = city_list
        return
        # if req['req']['url'].split('/')[-2] != 'region':
        #     return []
        #
        # city_list.csv = []
        # country_name = req['other_info']['country_name']
        # tree = HTML.fromstring(data, parser=etree.HTMLParser(encoding='utf-8'))
        # a_list = tree.xpath('//li[@class="sprite"]/a')
        # print len(a_list)
        # for a in a_list:
        #     city_name = a.xpath('./text()')[0]
        #     print city_name
        #     city_list.csv.append((country_name, city_name))

        print city_list[0][0], city_list[0][1]
        return city_list


if __name__ == '__main__':
    import json
    from mioji.dao import file_dao

    task = Task()
    task.source = 'agoda'

    spider = CityList(task)

    res = spider.crawl(cache_config={'enable':False})
    with open('city_list.csv','a+') as f:
        f.write('country,region,city,url\n')
        for country in spider.user_datas['city_dict']:
            for region in spider.user_datas['city_dict'][country]:
                for city in spider.user_datas['city_dict'][country][region]:
                    f.write("%s,%s,%s,%s\n"%(country,region,city[0],city[1]))
    print res
    headers = ['国家', '城市']
    file_dao.store_as_csv( 'city/agoda_city_en.csv', headers, res[0]['cityList_city'], row_count_cut=-1)
    file_dao.store_dict(res[0]['cityList_city'], 'agoda/citylist_en.json')
