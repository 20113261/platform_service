#!/usr/bin/python
# -*- coding: UTF-8 -*-


import json
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

from mioji.common import parser_except
from mioji.common.task_info import creat_hotelParams
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
#from mioji.models.city_models import get_suggest_city
from mioji.common.logger import logger
import hotellist_parse
import datetime
from datetime import timedelta
import re

url = 'http://www.booking.com/searchresults.zh-cn.html'
DATE_YEAR = '%Y'
DATE_MONTH = '%m'
DATE_DAY_MONTH = '%d'


def create_param(task_p, self_p):
    ages = ['A'] * task_p.adult
    for room in task_p.rooms_required:
        ages += room.child_age
    ages = [str(a) for a in ages]

    param = {
        'sid': '2fabc4030e6b847b9ef3b059e24c6b83',
        'aid': '376390',
        "label": "misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985:pl:ta:p1:p2:ac:ap1t1:neg:fi:tikwd-11455299683:lp9061505:li:dec:dm",
        # "sb": "1",
        # "src": "index",
        # "src_elem": "sb",
        "error_url": "http://www.booking.com/index.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA;sid=8ba5e9abe3eb9fcadf8e837d4d5a2464;sb_price_type=total&;",
        "ss": self_p['label'],  # "留尼汪圣保罗",#"圣保罗, 留尼汪"

        "ssne": self_p['label'],  # city_name+','+country, #"留尼汪圣保罗",
        "ssne_untouched": self_p['label'],  # city_name, #"留尼汪圣保罗",
        "checkin_year": task_p.format_check_in(DATE_YEAR),
        "checkin_month": int(task_p.format_check_in(DATE_MONTH)),
        "checkin_monthday": int(task_p.format_check_in(DATE_DAY_MONTH)),
        "checkout_year": task_p.format_check_out(DATE_YEAR),
        "checkout_month": int(task_p.format_check_out(DATE_MONTH)),
        "checkout_monthday": int(task_p.format_check_out(DATE_DAY_MONTH)),
        "room1": ','.join(ages),
        "no_rooms": task_p.rooms_count,
        "group_adults": task_p.adult,
        "group_children": task_p.child,
        "ss_raw": self_p['label'],  # city_name, #"留尼汪圣保罗",
        "ac_position": "0",
        # "ss_short": "",
        "dest_id": self_p['dest_id'],  # "ChIJBZBfqFSOgiERe2CfeoKwH24",
        "dest_type": self_p['dest_type'],  # "city",
        # "place_id": dest_id, #"ChIJBZBfqFSOgiERe2CfeoKwH24",
        # "place_id_lat": lat,#"-21.014047",
        # "place_id_lon": lon,#"55.269526999999925",
        # "place_types": "locality,political",
        # "search_pageview_id": "21204e0a46480251",
        # "search_selected": "true",
        # "search_pageview_id": "21204e0a46480251",
        # 'rows':30,
        "selected_currency": "CNY",
        'src': 'searchresults',
        'offset': 0,
    }
    print param
    return param

class HotelListSpider(Spider):
    source_type = 'bookingListHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
    }

    # 暂时不上线
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'bookingListHotel': {'required': ['room']}
    }

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
    def targets_request(self):
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
                temp_url = {}
                temp_url['label'] = re.search(u'(?<=ss=)([^&]+)',hotel_url).group()
                try:
                    temp_url['dest_id'] = re.search(r'(?<=dest_id=)([-0-9]+)(?=&)',hotel_url).group(1)
                except:
                    temp_url['dest_id'] = ''
                    logger.debug('没有解析到dest_id')
                try:
                    temp_url['dest_type'] =re.search(r'dest_type=([A-Za-z]+)',hotel_url).group(1)
                except:
                    temp_url['dest_type'] = ''
                    logger.debug('没有解析到dest_type')
                params = self.suggest_params(temp_url,check_in_date,check_out_date)

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
                #self_p = get_suggest_city('booking', mjcity_id)
                self_p = ''
                if not self_p:
                    raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                        'can’t find suggest config city:[{0}]'.format(mjcity_id))
            except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format(e))

            params = create_param(task_p, self_p)

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['hotel'])
        def first_page():
            '''
            data 如需要保存结果，指定data.key
            '''
            return {
                'req': {'url': url,'params': params},
                'data': {'content_type': 'html'},
            }
        yield first_page

    def parse_hotel(self,req,data):
        tree = data
        from lxml import html
        with open('booking.html','w+') as result:
            result.write(html.tostring(data))

        count_desc = tree.xpath('//div[contains(@role,"heading")]/h1/text()')

        if not count_desc:
                count_desc = tree.xpath('//div[contains(@role,"heading")]/h2/text()')

        count_desc = filter(lambda x:x!='\n',count_desc)
        print "count_desc:",count_desc

        hotel_count = re.search(r'[0-9,]+',count_desc[0]).group().replace(',','')
        print "hotel_count：",hotel_count
        return [hotel_count,]
if __name__ == '__main__':
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.get_proxy = simple_get_socks_proxy
    from mioji.common.task_info import Task

    task = Task()
    task.content = '10001&2&1&20170712'
    data_j = json.loads("""{"label_highlighted": "威尼斯, 威尼托大区, 意大利", "__part": 0, "type": "ci", "lc": "zh", "genius_hotels": "379", "rtl": 0, "label_multiline": "<span>威尼斯</span> 威尼托大区, 意大利", "dest_id": "-132007", "cc1": "it", "_ef": [{"name": "ac_popular_badge", "value": 1}], "nr_hotels_25": "3119", "label": "威尼斯, 威尼托大区, 意大利", "labels": [{"text": "威尼斯", "required": 1, "type": "city", "hl": 1}, {"text": "威尼托大区", "required": 1, "type": "region", "hl": 1}, {"text": "意大利", "required": 1, "type": "country", "hl": 1}], "__query_covered": 9, "flags": {"popular": 1}, "nr_hotels": "1953", "region_id": "914", "city_ufi": null, "label_cjk": "<span class='search_hl_cjk'>威尼斯</span> <span class='search_hl_cjk'>威尼托大区</span>, <span class='search_hl_cjk'>意大利</span>", "dest_type": "city", "hotels": "1953"}""")
    task.ticket_info = {
        'is_new_type': True,
        'suggest_type':1,
        'suggest': 'https://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ&sid=c475c497528f36b236ee530edb71bb6a&sb=1&src=index&src_elem=sb&error_url=https%3A%2F%2Fwww.booking.com%2Findex.zh-cn.html%3Flabel%3Dgen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ%3Bsid%3Dc475c497528f36b236ee530edb71bb6a%3Bsb_price_type%3Dtotal%26%3B&ss=%E4%B8%9C%E4%BA%AC&ssne=%E4%B8%9C%E4%BA%AC&ssne_untouched=%E4%B8%9C%E4%BA%AC&dest_id=-246227&dest_type=city&checkin_year=2017&checkin_month=12&checkin_monthday=11&checkout_year=2017&checkout_month=12&checkout_monthday=12&no_rooms=1&group_adults=2&group_children=0&from_sf=1',
        'check_in': '20171130',
        'stay_nights': '2',
        'occ': '2'
    }
    # task.extra['hotel'] = {'check_in':'20170503', 'nights':1, 'rooms':[{}] }
    spider = HotelListSpider()
    spider.task = task
    spider.crawl()
    result = spider.result
    # room和hotel数量不一致时因为hotel 没有去除推荐
    print result