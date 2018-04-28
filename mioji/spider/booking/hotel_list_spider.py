#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月19日

@author: dujun
'''

import json
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

from mioji.common import parser_except
from mioji.common.task_info import creat_hotelParams
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.models.city_models import get_suggest_city
from mioji.common.logger import logger
import hotellist_tag_parse
import hotellist_parse
import datetime
from datetime import timedelta
import re
from mioji.common import spider
spider.NEED_FLIP_LIMIT = False
# spider.pool.set_size(256)

url = 'http://www.booking.com/searchresults.zh-cn.html'
DATE_YEAR = '%Y'
DATE_MONTH = '%m'
DATE_DAY_MONTH = '%d'


# def create_param(task_p, self_p):
#     ages = ['A'] * task_p.adult
#     for room in task_p.rooms_required:
#         ages += room.child_age
#     ages = [str(a) for a in ages]
#
#     param = {
#         'sid': '2fabc4030e6b847b9ef3b059e24c6b83',
#         'aid': '376390',
#         "label": "misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985:pl:ta:p1:p2:ac:ap1t1:neg:fi:tikwd-11455299683:lp9061505:li:dec:dm",
#         # "sb": "1",
#         # "src": "index",
#         # "src_elem": "sb",
#         "error_url": "http://www.booking.com/index.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA;sid=8ba5e9abe3eb9fcadf8e837d4d5a2464;sb_price_type=total&;",
#         "ss": self_p['label'],  # "留尼汪圣保罗",#"圣保罗, 留尼汪"
#
#         "ssne": self_p['label'],  # city_name+','+country, #"留尼汪圣保罗",
#         "ssne_untouched": self_p['label'],  # city_name, #"留尼汪圣保罗",
#         "checkin_year": task_p.format_check_in(DATE_YEAR),
#         "checkin_month": int(task_p.format_check_in(DATE_MONTH)),
#         "checkin_monthday": int(task_p.format_check_in(DATE_DAY_MONTH)),
#         "checkout_year": task_p.format_check_out(DATE_YEAR),
#         "checkout_month": int(task_p.format_check_out(DATE_MONTH)),
#         "checkout_monthday": int(task_p.format_check_out(DATE_DAY_MONTH)),
#         "room1": ','.join(ages),
#         "no_rooms": task_p.rooms_count,
#         "group_adults": task_p.adult,
#         "group_children": task_p.child,
#         "ss_raw": self_p['label'],  # city_name, #"留尼汪圣保罗",
#         "ac_position": "0",
#         # "ss_short": "",
#         "dest_id": self_p['dest_id'],  # "ChIJBZBfqFSOgiERe2CfeoKwH24",
#         "dest_type": self_p['dest_type'],  # "city",
#         # "place_id": dest_id, #"ChIJBZBfqFSOgiERe2CfeoKwH24",
#         # "place_id_lat": lat,#"-21.014047",
#         # "place_id_lon": lon,#"55.269526999999925",
#         # "place_types": "locality,political",
#         # "search_pageview_id": "21204e0a46480251",
#         # "search_selected": "true",
#         # "search_pageview_id": "21204e0a46480251",
#         # 'rows':30,
#         "selected_currency": "CNY",
#         'src': 'searchresults',
#         'offset': 0,
#     }
#     print param
#     return param


class HotelListSpider(Spider):
    source_type = 'bookingListHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
        'filter': {},
        'room': {'version': 'InsertHotel_room4'}
    }

    # 暂时不上线
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'bookingListHotel': {'required': ['room']},
        'bookingFilterHotel': {'required': ['filter']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)

        self.task_info = None

        if self.task is not None:
            self.process_task_info()

    def process_task_info(self):
        """
        这个函数是为了将self.task的格式转换为咱们自己习惯的格式，总之就是为了方便自己，格式如下：
        self.ticket_info = {
        'is_new_type': False,
        'suggest_type':1,
        'suggest': "https://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=217af32acbc64a9dc8db8fd7d2f7aca9;checkin_month=9;checkin_monthday=27;checkin_year=2017;checkout_month=9;checkout_monthday=29;checkout_year=2017;class_interval=1;dest_id=20126162;dest_type=city;dtdisc=0;group_adults=2;group_children=0;inac=0;index_postcard=0;label_click=undef;no_rooms=1;offset=0;postcard=0;qrhpp=6398c3e46b4d2e9cdb31f60b0b675b4b-city-0;room1=A%2CA;sb_price_type=total;search_pageview_id=dea71cc5e6d1003f;search_selected=0;src=index;src_elem=sb;ss=%E9%98%BF%E6%AF%94%E6%9E%97%EF%BC%8C%E5%BE%B7%E5%85%8B%E8%90%A8%E6%96%AF%E5%B7%9E%EF%BC%8C%E7%BE%8E%E5%9B%BD;ss_all=0;ss_raw=%E9%98%BF%E6%AF%94%E6%9E%97%EF%BC%8C%E5%BE%B7%E5%85%8B%E8%90%A8%E6%96%AF%E5%B7%9E%EF%BC%8C%E7%BE%8E%E5%9B%BD;ssb=empty;sshis=0;origin=search;srpos=1",
        'check_in': '20180330',
        'stay_nights': '2',
        'occ': '2',
        'section_page':{'start_page':'5','end_page':'10'}
        }
        :return:
        """
        if hasattr(self.task,'ticket_info'):
            if isinstance(self.task.ticket_info, dict):
                self.task_info = dict()
                self.task_info['is_new_type'] = self.task.ticket_info.get('is_new_type',False)
                self.task_info['suggest_type'] = self.task.ticket_info.get('suggest_type',1)
                self.task_info['suggest'] = self.task.ticket_info.get('suggest',"https://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=217af32acbc64a9dc8db8fd7d2f7aca9;checkin_month=9;checkin_monthday=27;checkin_year=2017;checkout_month=9;checkout_monthday=29;checkout_year=2017;class_interval=1;dest_id=20126162;dest_type=city;dtdisc=0;group_adults=2;group_children=0;inac=0;index_postcard=0;label_click=undef;no_rooms=1;offset=0;postcard=0;qrhpp=6398c3e46b4d2e9cdb31f60b0b675b4b-city-0;room1=A%2CA;sb_price_type=total;search_pageview_id=dea71cc5e6d1003f;search_selected=0;src=index;src_elem=sb;ss=%E9%98%BF%E6%AF%94%E6%9E%97%EF%BC%8C%E5%BE%B7%E5%85%8B%E8%90%A8%E6%96%AF%E5%B7%9E%EF%BC%8C%E7%BE%8E%E5%9B%BD;ss_all=0;ss_raw=%E9%98%BF%E6%AF%94%E6%9E%97%EF%BC%8C%E5%BE%B7%E5%85%8B%E8%90%A8%E6%96%AF%E5%B7%9E%EF%BC%8C%E7%BE%8E%E5%9B%BD;ssb=empty;sshis=0;origin=search;srpos=1")
                self.task_info['check_in'] = self.task.ticket_info.get('check_in', '20180330')
                self.task_info['stay_nights'] = self.task.ticket_info.get('stay_nights','2')
                self.task_info['occ'] = self.task.ticket_info.get('occ','2')
                if self.task.ticket_info.get('section_page',{}).get("start_page","") and self.task.ticket_info.get('section_page',{}).get("end_page",""):
                    self.task_info['section_page'] = self.task.ticket_info.get('section_page',False)
                else:
                    self.task_info['section_page'] = False
            else:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format('task.ticket_info is not a dict.'))
        else:
            raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                'parse task occur some error:[{0}]'.format('task.ticket_info is not exist.'))

    def suggest_params(self,suggest_json,check_in,check_out):

        params = {
            'sid': '2fabc4030e6b847b9ef3b059e24c6b83',
            'aid': '376390',
            "label": "misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985:pl:ta:p1:p2:ac:ap1t1:neg:fi:tikwd-11455299683:lp9061505:li:dec:dm",
            "error_url": "http://www.booking.com/index.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA;sid=8ba5e9abe3eb9fcadf8e837d4d5a2464;sb_price_type=total&;",
            "ss": suggest_json['label'],  # "留尼汪圣保罗",#"圣保罗, 留尼汪"
            "ssne": suggest_json['label'],  # city_name+','+country, #"留尼汪圣保罗",
            "ssne_untouched": suggest_json['label'],  # city_name, #"留尼汪圣保罗",
            "checkin_year": check_in.year,
            "checkin_month": check_in.month,
            "checkin_monthday": check_in.day,
            "checkout_year": check_out.year,
            "checkout_month": check_out.month,
            "checkout_monthday": check_out.day,
            #"no_rooms": suggest_json.rooms_count,
            "group_adults": self.user_datas['adult'],
            "ss_raw": suggest_json['label'],  # city_name, #"留尼汪圣保罗",
            "ac_position": "0",
            "dest_id": suggest_json['dest_id'],  # "ChIJBZBfqFSOgiERe2CfeoKwH24",
            "dest_type": suggest_json['dest_type'],  # "city",
            "selected_currency": "CNY",
            'src': 'searchresults',
            'offset': 0,
        }
        return params

    def process_url(self,hotel_url,check_in,check_out,adult=2,room_type=None):
        hotel_url = re.sub(r'(checkin_month=)[0-9]*','\g<1>'+str(check_in.month),hotel_url)
        hotel_url = re.sub(r'(checkin_monthday=)[0-9]*','\g<1>'+str(check_in.day),hotel_url)
        hotel_url = re.sub(r'(checkin_year=)[0-9]*','\g<1>'+str(check_in.year),hotel_url)
        hotel_url = re.sub(r'(checkout_month=)[0-9]*','\g<1>'+str(check_out.month),hotel_url)
        hotel_url = re.sub(r'(checkout_monthday=)[0-9]*','\g<1>'+str(check_out.day),hotel_url)
        hotel_url = re.sub(r'(checkout_year=)[0-9]*','\g<1>'+str(check_out.year),hotel_url)
        hotel_url = re.sub(r'(group_adults=)[0-9]*','\g<1>'+str(adult),hotel_url)
        return hotel_url

    def targets_request(self):
        if self.task_info is None:
            self.process_task_info()
        if self.task.ticket_info.get('is_new_type'):
            self.user_datas['night'] = self.task.ticket_info.get('stay_nights')
            self.user_datas['adult'] = self.task.ticket_info.get('occ')
            hotel_url = self.task.ticket_info.get('suggest')
            check_in = self.task.ticket_info.get('check_in')
            check_in_date = datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:]))
            self.user_datas['check_in'] = str(check_in_date)[:10]
            check_out_date = datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])) + timedelta(
                int(self.user_datas['night']))
            self.user_datas['check_out'] = str(check_out_date)[:10]
            if self.task.ticket_info.get('suggest_type') == 1:
                hotel_url = self.process_url(hotel_url,check_in_date,check_out_date,self.user_datas['adult'])
                self.user_datas['mjcity_id'] = 'NULL'
            else:
                suggest_json = json.loads(self.task.ticket_info.get('suggest'))
                params = self.suggest_params(suggest_json,check_in_date,check_out_date)
                self.user_datas['mjcity_id'] = 'NULL'
        else:
            try:
                mjcity_id = self.task.content.split('&')[0]
                task_p = creat_hotelParams(self.task.content)
                self.user_datas['mjcity_id'] = mjcity_id
                suggest_city = get_suggest_city('booking', mjcity_id)
                self_p = suggest_city.get('suggest', None)
            except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format(e))
            is_new_type = suggest_city.get('is_new_type')
            if is_new_type == 0:
                if not self_p:
                    raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                        'can’t find suggest config city:[{0}]'.format(mjcity_id))
                params = self.suggest_params(self_p,task_p.check_in,task_p.check_out)
            elif is_new_type == 1:
                hotel_url = self_p.get('url')
                hotel_url = self.process_url(hotel_url,task_p.check_in,task_p.check_out,task_p.adult)

            self.user_datas['adult'] = task_p.adult
            self.user_datas['check_in'] = task_p.check_in
            self.user_datas['check_out'] = task_p.check_out
            self.user_datas['night'] = task_p.night


        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['hotel', 'room', 'filter'])
        def first_page():
            '''
            data 如需要保存结果，指定data.key
            '''
            new_type = self.task.ticket_info.get('is_new_type', None)
            suggest_type = self.task.ticket_info.get('suggest_type', None)
            if new_type and suggest_type or is_new_type:
                return {
                    'req': {'url': hotel_url},
                    'data': {'content_type': 'html'},
                    'user_handler': [self.parse_page_count],
                }
            else:
                return {
                    'req': {'url': url, 'params': params,'method': 'get' },
                    'data': {'content_type': 'html'},
                    'user_handler': [self.parse_page_count],
                }

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True, binding=['hotel', 'room'])
        def hotel_pages():
            # page by page
            print '$' * 100
            page_num = self.user_datas.get('page_num', 1)
            # 每页有多少的酒店
            page_size = self.user_datas.get('page_size', 15)
            pages = []
            new_type = self.task.ticket_info.get('is_new_type',None)
            suggest_type = self.task.ticket_info.get('suggest_type',None)
            if new_type and suggest_type or is_new_type:
                for p in xrange(2, page_num):
                    page_p = {}
                    page_p['rows'] = page_size
                    page_p['offset'] = (p - 1) * page_size
                    pages.append({
                        'req': {'url': hotel_url, 'params': page_p},
                        'data': {'content_type': 'html'}
                    })
            else:
                for p in xrange(2, page_num):
                    page_p = dict(params)
                    page_p['rows'] = page_size
                    page_p['offset'] = (p - 1) * page_size
                    pages.append({
                        'req': {'url': url, 'params': page_p},
                        'data': {'content_type': 'html'}
                    })

            return pages

        yield first_page
        if isinstance(self._crawl_targets_required,list) and len(self._crawl_targets_required) == 1 and 'filter' in self._crawl_targets_required:
            pass
        else:
            yield hotel_pages

    def parse_page_count(self, req, data):
        '''
        parse 开头解析，data
        '''
        try:
            dom = data
            page_num = int(dom.find_class('sr_pagination_link')[-1].xpath('./text()')[0])
            print 'parse_page', page_num
            self.user_datas['page_num'] = page_num
            self.user_datas['page_size'] = 15
        except:
            # 没有page了
            self.user_datas['page_num'] = 2
            self.user_datas['page_size'] = 15

    def parse_room(self, req, data):
        '''
        酒店例行
        '''
        # print 'parse_hotels_room', req, data
        # 找到验证票
        return hotellist_parse.parse_hotels_room(data, self.user_datas['check_in'], self.user_datas['check_out'],
                                                 self.user_datas['night'], self.user_datas['adult'],
                                                 self.user_datas['mjcity_id'])

    def parse_hotel(self, req, data):
        print req['resp'].url
        # 计算页数
        # print 'parse_hotels', req, data
        return hotellist_parse.parse_hotels_url(data)

    def parse_filter(self, req, data):
        return hotellist_tag_parse.parse_hotel_list_tag(req,data,self.user_datas['mjcity_id'])


if __name__ == '__main__':
    from mioji.common.utils import simple_get_socks_proxy
    from my_mongo import mongo_handle
    from mioji.common import spider
    spider.NEED_FLIP_LIMIT = False
    spider.pool.set_size(256)

    spider.slave_get_proxy = simple_get_socks_proxy
    from mioji.common.task_info import Task
    from new_booking.single_city_id import city_id_list

    count = 0
    # mongo_handle.open()

    for city_id_tuple in city_id_list:
        count += 1
        if count > 1:
            break
        city_id = city_id_tuple[0]
        temp_dict = {"city_id": city_id, "suggestion": None}

        task = Task()
        # task.content = city_id + '&2&1&20180330'
        task.content = '10006&2&1&20180330'
        # data_j = json.loads("""{"label_highlighted": "威尼斯, 威尼托大区, 意大利", "__part": 0, "type": "ci", "lc": "zh", "genius_hotels": "379", "rtl": 0, "label_multiline": "<span>威尼斯</span> 威尼托大区, 意大利", "dest_id": "-132007", "cc1": "it", "_ef": [{"name": "ac_popular_badge", "value": 1}], "nr_hotels_25": "3119", "label": "威尼斯, 威尼托大区, 意大利", "labels": [{"text": "威尼斯", "required": 1, "type": "city", "hl": 1}, {"text": "威尼托大区", "required": 1, "type": "region", "hl": 1}, {"text": "意大利", "required": 1, "type": "country", "hl": 1}], "__query_covered": 9, "flags": {"popular": 1}, "nr_hotels": "1953", "region_id": "914", "city_ufi": null, "label_cjk": "<span class='search_hl_cjk'>威尼斯</span> <span class='search_hl_cjk'>威尼托大区</span>, <span class='search_hl_cjk'>意大利</span>", "dest_type": "city", "hotels": "1953"}""")
        task.ticket_info = {
            'is_new_type': False,
            'suggest_type': 1,
            'suggest': "https://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=217af32acbc64a9dc8db8fd7d2f7aca9;checkin_month=9;checkin_monthday=27;checkin_year=2017;checkout_month=9;checkout_monthday=29;checkout_year=2017;class_interval=1;dest_id=20126162;dest_type=city;dtdisc=0;group_adults=2;group_children=0;inac=0;index_postcard=0;label_click=undef;no_rooms=1;offset=0;postcard=0;qrhpp=6398c3e46b4d2e9cdb31f60b0b675b4b-city-0;room1=A%2CA;sb_price_type=total;search_pageview_id=dea71cc5e6d1003f;search_selected=0;src=index;src_elem=sb;ss=%E9%98%BF%E6%AF%94%E6%9E%97%EF%BC%8C%E5%BE%B7%E5%85%8B%E8%90%A8%E6%96%AF%E5%B7%9E%EF%BC%8C%E7%BE%8E%E5%9B%BD;ss_all=0;ss_raw=%E9%98%BF%E6%AF%94%E6%9E%97%EF%BC%8C%E5%BE%B7%E5%85%8B%E8%90%A8%E6%96%AF%E5%B7%9E%EF%BC%8C%E7%BE%8E%E5%9B%BD;ssb=empty;sshis=0;origin=search;srpos=1",
            'check_in': '20180330',
            'stay_nights': '2',
            'occ': '2',
            'section_page': {'start_page': '0', 'end_page': '5'},
            'hotel_info':{
                "hotel_sort":"P+", # "P"以价格排序，"L"以距离排序，"R"按推荐排序 字符"+" or "-" 表示升序 or 降序排列, 如, "P+" 按价格升序排列, "L-" 按距离降序排列
                "has_breakfast": "Y", #str 是否有早餐"Y"表示有，"N"表示没有，
                "hotel_star": [1,2,5], # 1-5表示星级， 只有0表示不限
                "index_free": [1,13], # 爬取页码范围[1,13]只有两个数字，起始页 and 终止页
                "score":["9,10","8,9","7,8","0,7"], # 评分范围
                "bedtype":"O", # str "O"表示大床，"D"表示双床， "A"表示不限，
                "hotel_type":["E"], # "E"经济连锁，"B"品牌连锁，"L"客栈，"C"特色酒店，"A"不限
                "hotel_acilities": [], # 酒店设施
                "city_id": "", # 城市id
                "check_in": "", # "yyyymmdd"
                "check_out": "", # "yyyymmdd"
                "Landmark_Id": [], # 商圈 [] 源可以直接使用的商圈id
            }
        }
        spider = HotelListSpider()
        spider.task = task
        # print spider.crawl(required=['filter','hotel'])
        print spider.crawl(required=['filter'])
        result = spider.result
        # room和hotel数量不一致时因为hotel 没有去除推荐
        print len(result['hotel']), len(result['room']),len(result['filter'])
        if result['filter']:
            temp_result = result['filter']
            # mongo_handle.insert_one_to(temp_dict)
            print temp_result
        for hotel_result in result['hotel']:
            print hotel_result

        for room_result in result['room']:
            print room_result

