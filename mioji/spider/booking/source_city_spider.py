#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17/2/15 下午3:04
# @Author  : sws
# @Site    : 抓取booking网站上的所有的城市
# @File    : source_city_name.py
# @Software: PyCharm

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

from lxml import html as HTML, etree
import re

from mioji.common.task_info import Task
from mioji.common.spider import Spider, request, PROXY_REQ
# from mioji.common.parser_except import ParserException, TASK_ERROR

F_URL = 'https://www.booking.com/destination.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=ab35a990e72a15236369527c87c259c5'

'''
1 从 https://www.booking.com/destination.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=ab35a990e72a15236369527c87c259c5
2 选择对应的国家https://www.booking.com/destination/country/gb.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=ab35a990e72a15236369527c87c259c5
3 根据2返回的页面 获取全部的城市。
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

    def old_spider_tag(self):
        return CityList.__old_spider_tag

    def crawl_type(self):
        return CityList.__type

    def targets_parser(self):
        return CityList.__targets

    def parser_targets_version(self):
        return CityList.__targets_version

    def targets_request(self):

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_country():
            return {
                'req':{'url':F_URL},
                'data': {'content_type': 'string'},
                'user_handler':[self.parse_country],
               }

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True)
        def get_city():
            country_list = self.user_datas['country_list']

            region_list = []
            for co in country_list[:1]:
                region_list.append(
                    {
                        'req':{'url':co[1]},
                        'data': {'content_type': 'string'},
                        'other_info':{'country_name':co[0]},
                        # 'user_handler':[self.parse_region],
                    }
                )
            return region_list

        return [get_country, get_city]

    def parse_country(self, req, data):
        '''
            解析国家
        :return:
        '''
        tree = etree.HTML(data)
        print HTML.tostring(tree)

        ctry_list = []
        a_list = tree.xpath('//div[@class="flatList"]/a')
        print len(a_list)
        for a in a_list:
            country_name = a.xpath('./text()')[0]
            cou_url = 'http://www.booking.com'+a.xpath('./@href')[0]
            ctry_list.append((country_name, cou_url))
        print ctry_list
        self.user_datas['country_list'] = ctry_list


    def parse_cityName_city(self, req, data):
        if req['req']['url'].split('/')[-2] != 'country':
            return []



        city_list = []
        country_name = req['other_info']['country_name']
        tree = HTML.fromstring(data, parser=etree.HTMLParser(encoding='utf-8'))
        a_list = tree.xpath('//table[@class="general"][1]//a')
        print len(a_list)
        for a in a_list:
            city_name = a.xpath('./text()')[0]
            city_list.append((country_name, city_name))

        print city_list[0][0], city_list[0][1]
        return city_list


if __name__ == '__main__':
    import json

    task = Task()
    task.content = u'圣保罗'
    task.extra['hotel'] = {'check_in': '20170505', 'nights': 1, 'rooms': [{}]}
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{'adult':1, 'child':2}]}
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{'adult':1, 'child':2, 'child_age':[0, 6]}] * 2}
    print json.dumps(task.extra['hotel'])
    spider = CityList(task)
    print spider.crawl(cache_config={'enable':True, 'lifetime_sec':10*24*60*60})
    # print json.dumps(search(u'巴黎', 'Prser', '法国')[1])
