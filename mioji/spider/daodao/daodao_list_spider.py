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
        self.others_url = []
        self.save_page = defaultdict(list)

    def process_content(self):
        hotel_url = self.task.content
        self.hotel_url = hotel_url
        city_code = re.search(r'-g([\d]+)-', hotel_url).group(1)
        self.city_code = city_code
        city_name = re.search(r'-([a-zA-Z_]+)-Vacations', hotel_url).group(1)
        self.city_name = city_name

    def get_view_rest_url(self, req, data):
        root = data
        req_url = req['req']['url']
        try:
            view_url = ''
            view_aas = root.xpath('//div[@class="navLinks"]/ul/li[contains(@class, "attractions")]/a')
            if len(view_aas) > 0:
                view_url = view_aas[0].attrib.get('href', None)
        except Exception as e:
            print(traceback.format_exc(e))
            view_url = None
        try:
            rest_url = ''
            rest_aas = root.xpath('//div[@class="navLinks"]/ul/li[contains(@class, "restaurants")]/a')
            if len(rest_aas) > 0:
                rest_url = rest_aas[0].attrib.get('href', None)
        except Exception as e:
            print(traceback.format_exc(e))
            rest_url = None

        try:
            total_count_str = root.xpath('//li[contains(@class,"attractions")]/a/span[@class="typeQty"]/text()')
            total_count = re.search(r'[0-9]+', total_count_str[0]).group()
            self.user_datas['total_count'] = int(total_count)
            self.save_page[req_url] = [total_count, ]
        except Exception as e:
            print(traceback.format_exc(e))
        if view_url:
            self.view_url = urljoin(base_url, view_url)
        if rest_url:
            self.restaurant_url = urljoin(base_url, rest_url)

    def targets_request(self):

        self.process_content()
        tid = self.task.ticket_info.get('tid', '111')
        used_times = self.task.ticket_info.get('used_times', '2017')

        # 获取景点，餐厅的URL
        @request(retry_count=5, proxy_type=PROXY_REQ, user_retry_count=10,
                 store_page_name="city_first_page_{}_{}".format(tid, used_times))
        def hotel_url():
            return {
                'req': {'url': self.hotel_url},
                'data': {'content_type': 'html'},
                'user_handler': [self.get_view_rest_url]
            }

        yield hotel_url

        if self.view_url:
            @request(retry_count=5, proxy_type=PROXY_REQ, user_retry_count=10,
                     store_page_name="city_first_page_{}_{}".format(tid, used_times))
            def get_view_page_num():
                return {
                    'req': {'url': self.view_url},
                    'data': {'content_type': 'html'},
                    'user_handler': [self.parse_view_page_num]
                }

            yield get_view_page_num

            @request(retry_count=5, proxy_type=PROXY_REQ, binding=['view'], async=True, user_retry_count=10,
                     store_page_name="city_first_page_{}_{}".format(tid, used_times))
            def get_view_list_info():
                pages = []
                if not self.user_datas['view_pages']:
                    pages_count = self.user_datas['total_count'] / 30 + 1
                else:
                    pages_count = int(self.user_datas['view_pages'])
                for i, value in enumerate(range(pages_count)):
                    pages.append(
                        {
                            'req': {
                                'url': urljoin(base_url,
                                               page_view_url.format(self.city_code, str(i * 30), self.city_name)),
                                'headers': {
                                    'Host': 'www.tripadvisor.cn'
                                }
                            },
                            'data': {'content_type': 'html', 'page': i, 'type': 'attr'},
                        }
                    )
                return pages

            yield get_view_list_info

        if self.others_url:
            @request(retry_count=5, proxy_type=PROXY_REQ, binding=['view'], async=True, user_retry_count=10,
                     store_page_name="city_first_page_{}_{}".format(tid, used_times))
            def get_view_activity_info():
                other_city = []
                for activity_url in self.others_url:
                    url, count = activity_url.items()[0]
                    pages = count / 30 + 1
                    activity_page = []
                    # brand_str = re.search(r'Activities-([a-zA-Z0-9]+)-([a-zA-Z0-9]+)(?=-)', url).group(2)
                    # brand_index = url.find(brand_str)
                    for page in range(pages):
                        page_str = '-oa{0}'
                        req_url = url
                        page_str = page_str.format(page * 30)
                        req_url = req_url.replace('Activities', 'Activities{}'.format(page_str))
                        activity_page.append(
                            {
                                'req': {'url': req_url},
                                'data': {'content_type': 'html', 'page': page, 'type': 'shop-other'}
                            }
                        )
                    other_city.extend(activity_page)
                return other_city

            yield get_view_activity_info

        if self.restaurant_url:
            @request(retry_count=5, proxy_type=PROXY_REQ, user_retry_count=10,
                     store_page_name="city_first_page_{}_{}".format(tid, used_times))
            def get_restaurant_page_num():
                return {
                    'req': {'url': self.restaurant_url},
                    'data': {'content_type': 'html'},
                    'user_handler': [self.parse_restaurant_page_num]
                }

            # yield get_restaurant_page_num

            @request(retry_count=5, proxy_type=PROXY_REQ, binding=['restaurant'], async=True, user_retry_count=10,
                     store_page_name="city_first_page_{}_{}".format(tid, used_times))
            def get_restaurant_list_inifo():
                pages = []
                for i, value in enumerate(range(self.user_datas['restaurant_pages'])):
                    pages.append(
                        {
                            'req': {'url': urljoin(base_url, page_restaurant_url.format(self.city_code, str(i * 30),
                                                                                        self.city_name))},
                            'data': {'content_type': 'html', 'page': i, 'type': 'rest'}
                        }
                    )
                return pages

                # yield get_restaurant_list_inifo

    def parse_view_page_num(self, req, data):

        root = data
        try:
            self.user_datas['view_pages'] = int(root.xpath('//div[@class="pageNumbers"]/a')[-1].text)
            print(self.user_datas['view_pages'])
        except IndexError:
            self.user_datas['view_pages'] = None
            logger.debug(current_log_tag() + "不存在景点")

        # 添加购物链接
        try:
            shop_element = None
            for each_a_label in root.xpath('//*[@class="jfy_checkbox ui_input_checkbox multifilter"]/label/a'):
                try:
                    a_t_res = each_a_label.xpath('text()')
                    if a_t_res:
                        a_text = a_t_res[0]
                        if u'购物' in a_text:
                            shop_element = each_a_label
                            break
                except Exception:
                    pass

            if shop_element is not None:
                shop_text = shop_element.xpath('text()')[0]
                shop_url = urljoin(base_url, shop_element.xpath('@href')[0])
                shop_num = re.findall('(\d+)', shop_text)[0]
                self.others_url.append({shop_url: int(shop_num)})
        except Exception:
            pass

    def parse_restaurant_page_num(self, req, data):
        root = data
        try:
            self.user_datas['restaurant_pages'] = int(root.xpath("//div[@class='pageNumbers']/a")[-1].text)
            print(self.user_datas['restaurant_pages'])
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
                    temp[view.text]['page_type'] = req['data']['type']
                    temp[view.text]['page_id'] = req['data']['page']
                else:
                    continue
            self.restaurant_page_info.update(temp)
            print("抓取到数据的数量：", len(view_lists))
            return temp
        except:
            logger.debug(
                current_log_tag() + '【{0}解析错误】{1}'.format(self.parse_restaurant.__name__, parser_except.PARSE_ERROR))

    def parse_view(self, req, data):
        root = data
        temp = defaultdict(dict)
        url = req['req']['url']
        content = html.tostring(data)
        sign_str = re.search(r'Activities-c([a-zA-Z0-9]*?)(?=-)', url)
        try:
            view_lists = root.xpath("//div[@class='listing_info']")
            for view in view_lists:
                view = view.getchildren()[1].getchildren()[0]
                view_url = base_url + view.attrib.get('href', None)
                sid_temp = re.search(r'-d(\d+)-', view_url)
                judge_activity = re.search(r'Activities-c26', view_url)
                if sid_temp:
                    name = view.text
                    sid = sid_temp.group(1)
                    temp[sid]['view_url'] = view_url
                    temp[sid]['source_id'] = sid
                    temp[sid]['view_name'] = view.text
                    temp[sid]['page_type'] = req['data']['type']
                    temp[sid]['page_id'] = req['data']['page']
                    temp[sid]['name'] = name
                    # elif judge_activity:
                    #     count_str = view.text_content()
                    #     count = re.search(r'[0-9]+', count_str).group()
                    #     view_url = urljoin('https://www.tripadvisor.cn', view_url)
                    #     self.save_page[view_url] = [count, ]
                    #     self.others_url.append({view_url: int(count)})
                    #     logger.debug(current_log_tag() + '活动景点: url【{0}】,count:【{1}】'.format(view_url, count))

            if sign_str:
                sign_str = sign_str.group(0)
                for key in self.save_page.keys():
                    if sign_str in key:
                        self.save_page[key].append({url: len(temp)})
            else:
                self.save_page[url] = [len(temp), ]
            self.view_page_info.update(temp)
            logger.debug("请求的url:{0},解析到数据的数量：{1},抓取到的数据数量:{2}".format(url, len(view_lists), len(temp)))
            return temp
        except:
            logger.debug(
                current_log_tag() + '【{0}解析错误】{1}'.format(self.parse_restaurant.__name__, parser_except.PARSE_ERROR))
            print(traceback.format_exc())


if __name__ == "__main__":
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    from mioji.common.pool import pool

    # spider.slave_get_proxy = simple_get_socks_proxy
    spider.NEED_FLIP_LIMIT = False
    pool.set_size(1024)
    task = Task()
    spider = DaodaoViewSpider()
    # task.content = 'https://www.tripadvisor.com.hk/Tourism-g1899976-Burwood_Greater_Sydney_New_South_Wales-Vacations.html'
    # task.content = 'https://www.tripadvisor.cn/Tourism-g294212-Beijing-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g298184-Tokyo_Tokyo_Prefecture_Kanto-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g60763-New_York_City_New_York-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g294197-Seoul-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g186338-London_England-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g294452-Sofia_Sofia_Region-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g255368-Palmerston_North_Manawatu_Wanganui_Region_North_Island-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g57072-Monument_Valley_Utah-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g57106-Provo_Utah-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g609158-Kaitaia_Northland_Region_North_Island-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g503715-Longyearbyen_Spitsbergen_Svalbard-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g187492-Leon_Province_of_Leon_Castile_and_Leon-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g652095-Craiova_Dolj_County_Southwest_Romania-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g294265-Singapore-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g294452-Sofia_Sofia_Region-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g57106-Provo_Utah-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g187492-Leon_Province_of_Leon_Castile_and_Leon-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g57106-Provo_Utah-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g1055530-Mornington_Peninsula_Victoria-Vacations.html'
    task.content = 'https://www.tripadvisor.cn/Tourism-g294226-Bali-Vacations.html'
    # task.content = 'https://www.tripadvisor.cn/Tourism-g1081288-Dozza_Province_of_Bologna_Emilia_Romagna-Vacations.html'
    # task.content = 'https://www.tripadvisor.cn/Tourism-g187802-Maranello_Province_of_Modena_Emilia_Romagna-Vacations.html'

    task_list = [('10436','https://www.tripadvisor.cn/Tourism-g294452-Sofia_Sofia_Region-Vacations.html'),('10648','https://www.tripadvisor.cn/Tourism-g187777-Reggio_Calabria_Province_of_Reggio_Calabria_Calabria-Vacations.html'),('11424','https://www.tripadvisor.cn/Tourism-g187492-Leon_Province_of_Leon_Castile_and_Leon-Vacations.html'),('11444','https://www.tripadvisor.cn/Tourism-g503715-Longyearbyen_Spitsbergen_Svalbard-Vacations.html'),('12344','https://www.tripadvisor.cn/Tourism-g194758-Faenza_Province_of_Ravenna_Emilia_Romagna-Vacations.html'),('20096','https://www.tripadvisor.cn/Tourism-g294226-Bali-Vacations.html'),('30118','https://www.tripadvisor.cn/Tourism-g609158-Kaitaia_Northland_Region_North_Island-Vacations.html'),('30140','https://www.tripadvisor.cn/Tourism-g255368-Palmerston_North_Manawatu_Wanganui_Region_North_Island-Vacations.html'),('50117','https://www.tripadvisor.cn/Tourism-g57106-Provo_Utah-Vacations.html'),('60177','https://www.tripadvisor.cn/Tourism-g1081288-Dozza_Province_of_Bologna_Emilia_Romagna-Vacations.html'),('60178','https://www.tripadvisor.cn/Tourism-g187802-Maranello_Province_of_Modena_Emilia_Romagna-Vacations.html'),('60179','https://www.tripadvisor.cn/Tourism-g652095-Craiova_Dolj_County_Southwest_Romania-Vacations.html'),('60180','https://www.tripadvisor.cn/Tourism-g1055530-Mornington_Peninsula_Victoria-Vacations.html'),('60181','https://www.tripadvisor.cn/Tourism-g57072-Monument_Valley_Utah-Vacations.html'),('60182','https://www.tripadvisor.cn/Tourism-g562802-Westerstede_Lower_Saxony-Vacations.html'),('60183','https://www.tripadvisor.cn/Tourism-g41996-Birmingham_Michigan-Vacations.html')]

    for city_id, city_url in task_list:
        country_id = ''
        spider = DaodaoViewSpider()
        task = Task()
        task.content = city_url
        spider.task = task
        spider.crawl(required=['view'])
        print(spider.code)
        import pymysql

        conn = pymysql.connect(
            host='10.10.228.253',
            user='mioji_admin',
            password='mioji1109',
            charset='utf8',
            db='ServicePlatform'
        )
        cursor = conn.cursor()
        sql = '''SELECT *
        FROM list_attr_daodao_20171222a;
        INSERT IGNORE INTO list_attr_daodao_20171222a (source, source_id, city_id, country_id, hotel_url) VALUES (%s, %s, %s, %s, %s);'''
        for each in spider.result['view']:
            for k, v in each.items():
                view_url = v['view_url']
                sid = v['source_id']
                res = cursor.execute(sql, ('daodao', sid, city_id, country_id, view_url))
                conn.commit()
                print(res, sid, view_url)

# task.content = 'https://www.tripadvisor.cn/Attractions-g57072-Activities-Monument_Valley_Utah.html'
#     spider.task = task
#     spider.crawl(required=['view'])
#     print(spider.code)
#     # print spider.result['view']
#     # print("请求数目：", len(spider.result['view']))
#     # print(spider.page_store_key_list)
#     # print(spider.save_page)
#     # print(spider.view_page_info)
#     # print(spider.restaurant_page_info)
#     # print('Hello World')
#     import pymysql
#
#     conn = pymysql.connect(
#         host='10.10.228.253',
#         user='mioji_admin',
#         password='mioji1109',
#         charset='utf8',
#         db='ServicePlatform'
#     )
#     city_id = ''
#     country_id = ''
#     cursor = conn.cursor()
#     sql = '''SELECT *
# FROM list_attr_daodao_20171222a;
# INSERT IGNORE INTO list_attr_daodao_20171222a (source, source_id, city_id, country_id, hotel_url) VALUES (%s, %s, %s, %s, %s);'''
#     for each in spider.result['view']:
#         for k, v in each.items():
#             view_url = v['view_url']
#             sid = v['source_id']
#             res = cursor.execute(sql, ('daodao', sid, '60181', '501', view_url))
#             conn.commit()
#             print(res, sid, view_url)
#             # print spider.result['restaurant']
#             # print spider.view_page_info
