#!/usr/bin/python
# -*-coding:UTF-8 -*-

"""
    Created on 2017年3月28日
    目的：将qyer迁移到新框架
    @author:
"""
import sys
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
from math import ceil
from collections import defaultdict
import re
from urlparse import urljoin
from mioji.common.logger import logger
import requests
from mioji.common.parser_except import ParserException

reload(sys)
sys.setdefaultencoding('utf-8')

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'place.qyer.com',
    'Upgrade-Insecure-Requests': '1'
}


class QyerSpiderApi(Spider):
    # 抓取目标：穷游指定城市景点，美食，购物等信息列表
    source_type = 'qyerListInfo'

    # 数据目标：景点，美食，购物的全部URL
    targets = {
        'list': {}
    }

    old_spider_tag = {
        'qyerList': {'required': ['list']}
    }

    def __init__(self, task=None):
        super(QyerSpiderApi, self).__init__(task)
        self.headers = headers
        self.type = None
        self.city_url = None
        self.city_name = None
        self.save_city_page_url = defaultdict(list)
        self.save_city_info = defaultdict(dict)
        self.types = {
            'sight': 'attr',
            # 'food': 'rest',
            # 'shopping': 'shop'
        }
        self.types_result_num = {
            'attr': -1,
            'rest': -1,
            'shop': -1,
        }

    def targets_request(self):
        tid = self.task.ticket_info['tid']
        used_times = self.task.ticket_info['used_times']

        @request(retry_count=5, proxy_type=PROXY_REQ, user_retry_count=10,
                 store_page_name="city_first_page_{}_{}".format(tid, used_times))
        def city_first():
            url = self.task.content
            crawl_type = []
            for type in self.types.keys():
                crawl_type.append(
                    {
                        'req': {
                            'url': urljoin(url, type),
                            'headers': headers
                        },
                        'data': {
                            'content_type': 'html'
                        },
                        'user_handler': [self.get_type_info]
                    }
                )
            return crawl_type

        yield city_first

        @request(retry_count=5, proxy_type=PROXY_REQ, binding=['list'], user_retry_count=10,
                 store_page_name="city_branch_pages_{}_{}".format(tid, used_times))
        def branch_pages():
            city_page = []
            for city_name in self.save_city_info.keys():
                for type in self.save_city_info[city_name].keys():
                    pages = []
                    for page in range(1, self.save_city_info[city_name][type][0] + 1):
                        pages.append(
                            {
                                'req': {
                                    'url': 'http://place.qyer.com/poi.php?action=list_json',
                                    'data': {
                                        'page': page,
                                        'type': 'city',
                                        'pid': self.save_city_info[city_name][type][2],
                                        'sort': self.save_city_info[city_name][type][1],
                                        'subsort': 'all',
                                        'isnominate': '-1',
                                        'haslastm': 'false',
                                        # 'rank': 6
                                        'rank': '0'
                                    },
                                    'method': 'post',
                                    'city_name': city_name,
                                    'type': type,
                                },
                                'data': {'content_type': 'json'},
                            }
                        )
                    city_page.extend(pages)
            print "city_page_length:", len(city_page)
            print city_page
            return city_page

        yield branch_pages
        print "抓取url:", self.save_city_page_url

    def get_type_info(self, req, data):
        root = data
        type = req['req']['url'].split('/')[-1]
        self.type = type
        city_name = req['req']['url'].split('/')[-2]
        self.city_name = city_name
        if type == 'sight':
            page_info = root.xpath('//a[@data-bn-ipg="place-poilist-filter-classify-sight"]')[0].text
            total_num = int(re.findall(r'\d+', page_info)[0])
            self.types_result_num['attr'] = total_num
            page = int(ceil(total_num / 15.0))
            sort_info = root.xpath('//a[@data-bn-ipg="place-poilist-filter-classify-sight"]')[0]
            sort = int(sort_info.xpath('@data-id')[0])
            pid_info = root.xpath('//script[@type="text/javascript"]')[0].text
            pid = int(re.findall(r'\d+', pid_info)[0])
        if type == 'food':
            page_info = root.xpath('//a[@data-bn-ipg="place-poilist-filter-classify-food"]')[0].text
            total_num = int(re.findall(r'\d+', page_info)[0])
            self.types_result_num['rest'] = total_num
            page = int(ceil(total_num / 15.0))
            sort_info = root.xpath('//a[@data-bn-ipg="place-poilist-filter-classify-food"]')[0]
            sort = int(sort_info.xpath('@data-id')[0])
            pid_info = root.xpath('//script[@type="text/javascript"]')[0].text
            pid = int(re.findall(r'\d+', pid_info)[0])
        if type == 'shopping':
            # page_info = root.xpath('//a[@data-bn-ipg="place-city-poi-moreshopping"]')[0].text
            page_info = root.xpath('//a[@data-bn-ipg="place-poilist-filter-classify-shopping"]')[0].text
            total_num = int(re.findall(r'\d+', page_info)[0])
            self.types_result_num['shop'] = total_num
            page = int(ceil(total_num / 15.0))
            sort_info = root.xpath('//a[@data-bn-ipg="place-poilist-filter-classify-shopping"]')[0]
            sort = int(sort_info.xpath('@data-id')[0])
            pid_info = root.xpath('//script[@type="text/javascript"]')[0].text
            pid = int(re.findall(r'\d+', pid_info)[0])
        self.save_city_info[city_name][type] = [page, sort, pid]
        print self.save_city_info

    def parse_list(self, req, data):
        if data['result'] != 'ok':
            raise ParserException(parser_error_code=ParserException.PROXY_INVALID)
        # if dict(req['req']).has_key('city_name'):
        #     city_name = req['req']['city_name']
        # if dict(req['req']).has_key('type'):
        #     city_type = req['req']['type']
        temp_list = []
        for list in data['data']['list']:
            temp_list.append((
                list['id'],
                urljoin('http:', list['url']),
                req['req']['data']['page']
            ))
        # self.save_city_page_url[city_name + '_' + city_type].extend(temp_list)
        # return {self.types[city_type]: temp_list}
        return temp_list


# class NewQyerSpider(Spider):
#     # 抓取目标：穷游指定城市景点，美食，购物等信息列表
#     source_type = 'qyerListInfo'
#
#     # 数据目标：景点，美食，购物的全部URL
#     targets = {
#         'list': {}
#     }
#
#     old_spider_tag = {
#         'qyerList': {'required': ['list']}
#     }
#
#     def __init__(self, task=None):
#         super(NewQyerSpider, self).__init__(task)
#         self.headers = headers
#         self.save_data = defaultdict(list)
#         self.types = {
#             'sight': 'attr',
#             # 'food': 'rest',
#             'shopping': 'shop'
#         }
#
#     def targets_request(self):
#         # url = self.task.content
#         sight_page = 50
#         shop_page = 5
#         city_name = self.task.content.split('/')[-1]
#
#         @request(retry_count=5, proxy_type=PROXY_REQ)
#         def first_page():
#             city_page = []
#             for crawl_type in self.types.keys():
#                 pages = []
#                 if crawl_type == 'sight':
#                     for page in range(1, sight_page):
#                         pages.append(
#                             {
#                                 'req': {
#                                     'url': 'http://place.qyer.com/bavaria/sight/',
#                                     'params': {'page': page},
#                                     'method': 'get'
#                                 },
#                                 'data': {'content_type': 'html'},
#                                 'city_type': '_'.join([city_name, crawl_type])
#                             }
#                         )
#                 city_page.extend(pages)
#             return city_page
#
#         @request(retry_count=5, proxy_type=PROXY_REQ, binding=['list'], async=False)
#         def branch_pages():
#             city_page = []
#             for crawl_type in self.types.keys():
#                 pages = []
#                 if crawl_type == 'sight':
#                     for page in range(1, sight_page):
#                         pages.append(
#                             {
#                                 'req': {
#                                     'url': urljoin(self.task.content, crawl_type),
#                                     'params': {'page': page},
#                                     'method': 'get'
#                                 },
#                                 'data': {'content_type': 'html'},
#                                 'city_type': '_'.join([city_name, crawl_type])
#                             }
#                         )
#                 # elif crawl_type == 'shopping':
#                 #     for page in range(1, shop_page):
#                 #         req_url = urljoin(url, crawl_type)
#                 #         req_url = urljoin(req_url + '/', 'tag279')
#                 #         pages.append(
#                 #             {
#                 #                 'req': {
#                 #                     'url': req_url,
#                 #                     'params': {'page': page},
#                 #                     'method': 'get'
#                 #                 },
#                 #                 'data': {'content_type': 'html'},
#                 #                 'city_type': '_'.join([city_name, crawl_type])
#                 #             }
#                 #         )
#                 city_page.extend(pages)
#             return city_page
#
#         yield branch_pages
#
#     def first_page_handler(self, req, data):
#         pass
#
#     def parse_list(self, req, data):
#         root = data
#         city_type = req['city_type']
#         try:
#             data_list = root.xpath('//ul[@id="poiLists"]/li/div/h3/a/@href')
#             id_list = root.xpath('//ul[@id="poiLists"]/li/div/p[@data-type="poi"]/@data-pid')
#             data_name = root.xpath('//ul[@id="poiLists"]/li/div/h3/a/text()')
#             data_list = map(lambda x: urljoin('http:', x), data_list)
#         except Exception as e:
#             logger.debug('请求出现异常,请求的url:【{0}】'.format(req['req']['url']))
#         result = zip(id_list, data_list)
#         # self.save_data[city_type].extend(result)
#         print '*' * 30, "type:", city_type, '*' * 30
#         for name in data_name:
#             name = name.replace('\r\n', '').strip()
#             print "景点名称：", name
#         return result


if __name__ == "__main__":
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy
    mioji.common.spider.NEED_FLIP_LIMIT = False

    task = Task()
    task.content = 'http://place.qyer.com/tokyo/'
    # task.content = 'http://place.qyer.com/paris/'
    task.content = 'http://place.qyer.com/new-york/'
    task.content = 'http://place.qyer.com/paris/'
    task.content = 'http://place.qyer.com/taif/'
    task.content = 'http://place.qyer.com/praslin-island/'
    task.content = 'http://place.qyer.com/bavaria/'
    task.ticket_info = {
        'tid': '',
        'used_times': 3
    }
    spider.task = task
    # spider = NewQyerSpider(task)
    spider = QyerSpiderApi(task)
    spider.crawl()
    print('=================================================================================0')
    print(spider.result['list'])
    print(spider.page_store_key_list)
    print(spider.types_result_num)

    print('=================================================================================1')
