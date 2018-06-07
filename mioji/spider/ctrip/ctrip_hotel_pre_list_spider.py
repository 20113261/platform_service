#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import sys
import time
import json
import datetime
import execjs
from urllib import urlencode
from mioji.common.mioji_struct import HotelList, HotelListSegment
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
# from mioji.models.city_models import get_suggest_city
from mioji.common import parser_except
from lxml import etree
from ctrip_pre_list_config import config

reload(sys)
sys.setdefaultencoding('utf-8')
size_pat = re.compile(r'\d+-?\d+', re.S)
base_url = 'http://hotels.ctrip.com/international/tool/AjaxHotelList.aspx'
headers = {
    'Host': 'hotels.ctrip.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Accept': '*/*',  # 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    'Connection': 'keep-alive',
    'Referer': 'http://hotels.ctrip.com/international/london338'
}


def getCallback(mix_n):
    try:
        ph_runtime = execjs.get('PhantomJS')
    except:
        raise parser_except.ParserException(97, '未配置PhantomJS')
    mixjs = ph_runtime.compile("""

        function generateMixed (n) {
        var chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'];
        var res = '';

        for (var i = 0; i < n; i++) {
            var id = Math.ceil(Math.random() * 51);
            res += chars[id];
        }

        return res;
    }
    """)
    call_back = mixjs.call("generateMixed", mix_n)
    return call_back


class CtripPreListSpider(Spider):
    source_type = 'ctripListHotel'
    targets = {"hotel": {'version': 'InsertNewHotel'}}

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'ctripListHotel': {'required': ['hotel']}
    }

    def __init__(self, task=None):
        super(CtripPreListSpider, self).__init__(task)
        self.no_repeat_dict = {'HotelRoomData': {'subRoomList': [], 'roomList': []}}
        self.callback_req = ''
        self.callback_param = ''
        self.headers = headers
        self.RemainingSegmentationNo_list = []
        self.config = config
        self.orderby = ""
        self.ordertype = "1"
        self.score = ""
        self.star = ""
        self.has_breakfast = ""
        self.bed_type = ""
        self.equip = ""
        self.landmark_id = ""
        self.page_flag = False
        self.rooms = 1
        self.adults = 1
        self.childs = '1'
        self.brand_id = ""
        if task:
            self.process_info()

    def process_info(self):
        self.city_id = self.task.ticket_info['hotel_info'].get("city_id")
        check_in = self.task.ticket_info['hotel_info'].get("checkin")
        check_out = self.task.ticket_info['hotel_info'].get("checkout")
        self.check_in = check_in[0:4] + '-' + check_in[4:6] + '-' + check_in[6:]
        self.check_out = check_out[0:4] + '-' + check_out[4:6] + '-' + check_out[6:]
        landmark_id = self.task.ticket_info['hotel_info'].get("Landmark_id")
        hotel_sort = self.task.ticket_info['hotel_info'].get("hotel_sort")
        has_breakfast = self.task.ticket_info['hotel_info'].get("has_breakfast")
        hotel_star = self.task.ticket_info['hotel_info'].get("hotel_star")
        score = self.task.ticket_info['hotel_info'].get("score")
        self.index_free = self.task.ticket_info['hotel_info'].get("page_num")
        bed_type = self.task.ticket_info['hotel_info'].get("bed_type")
        acilities = self.task.ticket_info['hotel_info'].get("hotel_acilities")
        brand_id = self.task.ticket_info['hotel_info'].get("brand_id")
        if score:
            score = score[0]
            score_l = score.split(",")
            self.score = str(int(score_l[0]) / 2)
        if hotel_sort:
            for sort_dict in self.config[0]['hotel_sort']:
                if sort_dict.has_key(hotel_sort):
                    self.orderby = sort_dict[hotel_sort][0]
                    self.ordertype = sort_dict[hotel_sort][1]
        if has_breakfast:
            for fast_dict in self.config[1]['has_breakfast']:
                if fast_dict.has_key(has_breakfast):
                    self.has_breakfast = fast_dict[has_breakfast]
        if hotel_star:
            star_str = ""
            for star in hotel_star:
                if star == "0":
                    self.star = ""
                elif star == "1":
                    pass
                else:
                    for star_dict in self.config[2]['hotel_star']:
                        if star_dict.has_key(star):
                            star_str += star_dict[star] + ","
                    self.star = star_str[:-1]
        if bed_type:
            for bed_dict in self.config[3]['bed_type']:
                if bed_dict.has_key(bed_type):
                    self.bed_type = bed_dict[bed_type]
        if acilities:
            self.equip = ",".join(acilities)
        if landmark_id:
            self.landmark_id = ",".join(landmark_id)
        if brand_id:
            self.brand_id = ",".join(brand_id)
        room_infos = self.task.ticket_info.get("room_info",[])
        if room_infos:
            self.rooms = len(room_infos)
            self.adults = 0
            self.childs = ''
            for room_info in room_infos:
                adults = len(room_info["adult_info"])
                self.adults += adults
                childs = room_info["child_info"]
                for child in childs:
                    self.childs += "-"+str(child)

        # 如果没有在获取eleven过程中异常抛出22错误 表示获取的eleven信息不完整
        '''
        mixjs = execjs.compile("""

            function generateMixed (n) {
            var chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'];
            var res = '';

            for (var i = 0; i < n; i++) {
                var id = Math.ceil(Math.random() * 51);
                res += chars[id];
            }

            return res;
        }
        """)
        call_back = mixjs.call("generateMixed",mix_n)
        '''
        call_back = getCallback(17)
        self.callback_param = call_back
        callback_req = "http://hotels.ctrip.com/international/Tool/cas-ocanball.aspx?callback=%s&" % (
            str(call_back))
        return callback_req

    def targets_request(self):
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_request():
            """
                获取 eleven
            """
            call_back_req = self.process_info()
            return {
                'req': {'url': call_back_req, 'headers': self.headers, 'params': {'_': str(int(time.time() * 1000))}},
                'data': {'content_type': 'text'},
                'user_handler': [self.first_user_handler]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel, async=True)
        def second_request():
            """
                酒店筛选项请求
            """
            req_l = []
            req_list = self.get_form_data()
            for data in req_list:
                print data
                req_l.append({
                    'req': {'url': base_url, 'headers': {'Referer': 'http://hotels.ctrip.com/international/london338'}, 'method': 'post', 'data': data},
                    'data': {'content_type': 'json'},
                })
            return req_l

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def get_total_page():
            """
                获取总页数请求
            """
            first_req = self.get_form_data()[0]
            return {
                'req': {'url': base_url, 'headers': {'Referer': 'http://hotels.ctrip.com/international/london338'}, 'method': 'post', 'data': first_req},
                'data': {'content_type': 'json'},
                'user_handler': [self.get_total_page]
            }

        # return [first_request, second_request, get_total_page]
        yield first_request
        if self.index_free == -1:
            yield get_total_page
        yield second_request

    def get_total_page(self, req, data):
        total_page = data.get('totalPage', '1')
        self.page_flag = True
        self.total_page = total_page

    def first_user_handler(self, req, data):
        """
        解析页面获取eleven
        :param req:
        :param data:
        :return:
        """
        # city_id, hotel_id, check_in_form, check_out_form, room_num, child_num, cid = self.user_datas['infomation']
        eleven = ''

        try:
            ph_runtime = execjs.get('PhantomJS')
        except:
            raise parser_except.ParserException(97, '未配置PhantomJS')
        try:
            encode_js_list = eval(re.findall('\[\d.+\d\]', data)[0])
            sub_key = int(re.findall('fromCharCode.+-\d+', data)[0].split('-')[1])
            encode_js_list = [x - sub_key for x in encode_js_list]
            encode_js = ''.join(chr(x) for x in encode_js_list)

            func_err = re.findall('\w+\(new Function', encode_js)[0]  # 替换最后return的内容
            href = re.findall('/international/.+?\"', encode_js)[0][:-1]  # 替换判断的href地址

            pat3 = re.compile(r'\'length\';(.*?&&.*?&&.*?&&.*?\);).*')  # 删掉判断模拟器会进入的错误分支代码
            replace_str2 = pat3.findall(encode_js)

            encode_js = encode_js.replace(';!function()', 'function run()') \
                            .replace(func_err, 'return(')[:-3] \
                .replace(replace_str2[0], '') \
                .replace(href, '')
            res = ph_runtime.compile(encode_js).call('run')
            eleven = re.search(r'"(.*?)"', res).group(1)
            if eleven == None:
                parser_except.ParserException(parser_except.PROXY_INVALID, 'ctripHotel :: 获取eleven失败')
        except Exception as e:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, 'ctripHotel :: 获取eleven失败')
        print eleven, '*' * 100
        self.user_datas['eleven'] = eleven

    def get_form_data(self):
        """
         组建form表单数据
        """
        req_list = []

        if self.index_free != -1:
            end_page = int(self.index_free)
        else:
            if self.page_flag is False:
                end_page = 1
            else:
                end_page = self.total_page
        for page in range(1, end_page + 1):
            data = {
                "checkIn": self.check_in,
                "checkOut": self.check_out,
                "destinationType": "1",
                "IsSuperiorCity": "1",
                "cityId": self.city_id,
                "cityPY": "",
                "rooms": self.adults,
                "childNum": str(self.adults)+self.childs,
                "roomQuantity": self.rooms,
                "pageIndex": page,
                "keyword": "",
                "keywordType": "",
                "LandmarkId": "",
                "districtId": "",
                "zone": self.landmark_id,
                "metrostation": "",
                "metroline": "",
                "price": "",
                "star": self.star,
                "equip": self.equip,
                "brand": self.brand_id,
                "group": "",
                "fea": "",
                "htype": "",
                "coupon": "",
                "a": "",
                "orderby": self.orderby,
                "ordertype": self.ordertype,
                "isAirport": "0",
                "hotelID": "",
                "priceSwitch": "",
                "lat": "",
                "lon": "",
                "clearHotelName": "",
                "promotionid": "",
                "commentrating": self.score,
                "breakfast": self.has_breakfast,
                "bed": self.bed_type,
                "eleven": self.user_datas.get('eleven', "")
            }
            req_list.append(data)
        return req_list

    def parse_hotel(self, req, data):
        hotel_info = data['HotelPositionJSON']
        hotellist = HotelList()
        hotellist.qid = self.task.ticket_info['hotel_info'].get("qid", "")
        hotellist.source = 'ctrip'
        hotellist.req_info = self.task.ticket_info['hotel_info']
        hotellist.page_num = data.get("DigDataEDMString").get("pageindex")
        hoteldetail = data["hotelListHtml"]
        select = etree.HTML(hoteldetail)
        for hotel in hotel_info:
            hotel_seg = HotelListSegment()
            try:
                hotel_seg.price = float(hotel['price'])
            except Exception as e:
                hotel_seg.price = float(-1)
            hotel_seg.hotel_id = str(hotel['id'])
            info = select.xpath("//div[@id='{}']/div/div[@class='J_hotelDynamicInfo']/span[@class='hlist_item_soldout"
                                "']/text()".format(hotel_seg.hotel_id))
            if info:
                hotel_seg.price = float(-1)
            hotel_seg.hotel_name = re.sub('(\([\s\S]+?\))', '', hotel['name']).encode('utf8')
            hotel_seg.ccy = "CNY"
            hotel_seg.hotel_url = 'http://hotels.ctrip.com'+hotel["url"]
            hotellist.append_hotel_info_to_list(hotel_seg)
        res = hotellist.return_hotel_info_all()
        return res


if __name__ == "__main__":
    from mioji.common.utils import simple_get_socks_proxy_new, httpset_debug
    from mioji.common import spider

    # spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    task.ticket_info['hotel_info'] = {
        "hotel_sort": "R",
        "has_breakfast": 1,
        "hotel_star": [],
        "page_num": -1,
        "score": [],
        "bed_type": 1,
        "hotel_type": [],
        "hotel_acilities": [],
        "city_id": "511",
        "checkin": "20180501",
        "checkout": "20180503",
        "Landmark_id": [],
        "brand_id": ["121,32,120,10,119,118", "18,130,129"]
    }
    # task.ticket_info["room_info"] = [
    #     {"adult_info": [33, 44, 55], "child_info": [7, 12, ]},
    #     {"adult_info": [33, 44, 55], "child_info": [7, 12, ]},
    # ]
    # task.suggest = "Malden|\xe9\xa9\xac\xe5\xb0\x94\xe7\x99\xbb\xef\xbc\x8c\xe9\xa9\xac\xe8\x90\xa8\xe8\xaf\xb8\xe5\xa1\x9e\xe5\xb7\x9e\xef\xbc\x8c\xe7\xbe\x8e\xe5\x9b\xbd|city|26951|malden|26951|malden|\xe9\xa9\xac\xe5\xb0\x94\xe7\x99\xbb|4|0||-18000"
    # task.ticket_info['hotel_info'] = {
    #     "qid": "",
    #     "has_breakfast": 1,
    #     "page_num": 5,
    #     "bedtype": 1,
    #     "city_id": "347",
    #     "check_in": "20180501",
    #     "check_out": "20180503",
    # }
    spider = CtripPreListSpider()
    spider.task = task
    spider.crawl()
    print(json.dumps(spider.result, ensure_ascii=False))
