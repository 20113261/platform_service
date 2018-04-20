# -*- coding:utf-8 -*-

"""
    daodao景点，餐厅抓取
"""
from mioji.common.logger import logger
from mioji.common import parser_except
from mioji.common.func_log import current_log_tag
from mioji.common.task_info import Task
from mioji.common.parser_except import PROXY_INVALID, PROXY_FORBIDDEN
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
import re
from lxml import html
from collections import defaultdict
from urlparse import urljoin
import traceback

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
}

page_view_url = "/Attractions-g{0}-Activities-oa{1}-{2}.html#ATTRACTION_LIST"
page_restaurant_url = "/Restaurants-g{0}-oa{1}-{2}.html#EATERY_LIST_CONTENTS"
base_url = 'https://www.tripadvisor.cn/'


class DaodaoViewSpider(Spider):
    source_type = "DaodaoListInfo"

    # 抓取数据： 景点，餐厅的URL，以及它们的sid
    targets = {
        'view': {},
        'restaurant': {}
    }

    old_spider_tag = {
        'daodaoView': {'required': ['view']},
        'daodaoRest': {'required': ['restaurant']}
    }

    def __init__(self):
        super(DaodaoViewSpider, self).__init__()
        self.header = headers
        self.view_url = None
        self.restaurant_url = None
        self.hotel_url = None
        self.view_page_info = defaultdict(dict)
        self.restaurant_page_info = defaultdict(dict)

    def process_content(self):
        hotel_url = self.task.content
        self.hotel_url = hotel_url
        city_code = re.search(r'-g([\d]+)-', hotel_url).group(1)
        self.city_code = city_code
        city_name = re.search(r'-([a-zA-Z_]+)-Vacations', hotel_url).group(1)
        self.city_name = city_name

    def get_view_rest_url(self, req, data):
        root = data
        try:
            view_url = ''
            view_aas = root.xpath('//div[@class="navLinks"]/ul/li[contains(@class, "attractions")]/a')
            if len(view_aas) > 0:
                view_url = view_aas[0].attrib.get('href', None)
        except Exception as e:
            print traceback.format_exc(e)
            view_url = None
        try:
            rest_url = ''
            rest_aas = root.xpath('//div[@class="navLinks"]/ul/li[contains(@class, "restaurants")]/a')
            if len(rest_aas)> 0:
                rest_url = rest_aas[0].attrib.get('href', None)
        except Exception as e:
            print traceback.format_exc(e)
            rest_url = None

        if view_url:
            self.view_url = urljoin(base_url, view_url)
        if rest_url:
            self.restaurant_url = urljoin(base_url, rest_url)

    def targets_request(self):

        self.process_content()

        # 获取景点，餐厅的URL
        @request(retry_count=5, proxy_type=PROXY_REQ)
        def hotel_url():
            return {
                'req': {'url': self.hotel_url},
                'data': {'content_type': 'html'},
                'user_handler': [self.get_view_rest_url]
            }

        yield hotel_url

        if self.view_url:
            @request(retry_count=5, proxy_type=PROXY_REQ)
            def get_view_page_num():
                return {
                    'req': {'url': self.view_url},
                    'data': {'content_type': 'html'},
                    'user_handler': [self.parse_view_page_num]
                }

            yield get_view_page_num

            @request(retry_count=5, proxy_type=PROXY_REQ, binding=['view'], async=True)
            def get_view_list_info():
                pages = []
                for i, value in enumerate(range(self.user_datas['view_pages'])):
                    pages.append(
                        {
                            'req': {'url': urljoin(base_url,
                                                   page_view_url.format(self.city_code, str(i * 30), self.city_name))},
                            'data': {'content_type': 'html'},
                        }
                    )
                return pages

            yield get_view_list_info

        if self.restaurant_url:
            @request(retry_count=5, proxy_type=PROXY_REQ)
            def get_restaurant_page_num():
                return {
                    'req': {'url': self.restaurant_url},
                    'data': {'content_type': 'html'},
                    'user_handler': [self.parse_restaurant_page_num]
                }

            yield get_restaurant_page_num

            @request(retry_count=5, proxy_type=PROXY_REQ, binding=['restaurant'], async=True)
            def get_restaurant_list_inifo():
                pages = []
                for i, value in enumerate(range(self.user_datas['restaurant_pages'])):
                    pages.append(
                        {
                            'req': {'url': urljoin(base_url, page_restaurant_url.format(self.city_code, str(i * 30),
                                                                                        self.city_name))},
                            'data': {'content_type': 'html'}
                        }
                    )
                return pages

            yield get_restaurant_list_inifo

    def parse_view_page_num(self, req, data):
        root = data
        try:
            self.user_datas['view_pages'] = int(root.xpath('//div[@class="pageNumbers"]/a')[-1].text)
            print self.user_datas['view_pages']
        except IndexError:
            self.user_datas['view_pages'] = 1
            logger.debug(current_log_tag() + "不存在景点")

    def parse_restaurant_page_num(self, req, data):
        root = data
        try:
            self.user_datas['restaurant_pages'] = int(root.xpath("//div[@class='pageNumbers']/a")[-1].text)
            print self.user_datas['restaurant_pages']
        except IndexError:
            self.user_datas['restaurant_pages'] = 1
            logger.debug(current_log_tag() + "不存在餐厅")

    def parse_restaurant(self, req, data):
        root = data
        temp = defaultdict(dict)
        try:
            view_lists = root.xpath("//div[@class='title']/a")
            for view in view_lists:
                view_url = base_url + view.attrib.get('href')
                sid_temp = re.search(r'-d(\d+)', view_url)
                if sid_temp:
                    sid = sid_temp.group(1)
                    temp[view.text]['view_url'] = view_url
                    temp[view.text]['source_id'] = sid
                    temp[view.text]['view_name'] = view.text
                else:
                    continue
            self.restaurant_page_info.update(temp)
            print "抓取到的数据：", temp, "抓取到数据的数量：", len(view_lists)
            return temp
        except:
            logger.debug(
                current_log_tag() + '【{0}解析错误】{1}'.format(self.parse_restaurant.__name__, parser_except.PARSE_ERROR))

    def parse_view(self, req, data):
        root = data
        temp = defaultdict(dict)
        try:
            view_lists = root.xpath("//div[@class='listing_info']")
            for view in view_lists:
                view = view.getchildren()[1].getchildren()[0]
                view_url = base_url + view.attrib.get('href', None)
                sid_temp = re.search(r'-d(\d+)-', view_url)
                if sid_temp:
                    sid = sid_temp.group(1)
                    temp[view.text]['view_url'] = view_url
                    temp[view.text]['source_id'] = sid
                    temp[view.text]['view_name'] = view.text
                else:
                    continue
            self.view_page_info.update(temp)
            print "抓取到的数据：", temp, "抓取到数据的数量：", len(view_lists)
            return temp
        except:
            logger.debug(
                current_log_tag() + '【{0}解析错误】{1}'.format(self.parse_restaurant.__name__, parser_except.PARSE_ERROR))
            print traceback.format_exc()


if __name__ == "__main__":
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.get_proxy = simple_get_socks_proxy
    task = Task()
    spider = DaodaoViewSpider()
    # task.content = 'https://www.tripadvisor.com.hk/Tourism-g1899976-Burwood_Greater_Sydney_New_South_Wales-Vacations.html'
    # task.content = 'https://www.tripadvisor.cn/Tourism-g294212-Beijing-Vacations.html'
    spider.task = task
    spider.crawl(required=['view', 'restaurant'])
    print spider.code
    print spider.result['view']
    print spider.result['restaurant']
    # print spider.view_page_info
