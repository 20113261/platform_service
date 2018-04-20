#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年3月30日

@author: chenjinhui
"""
import re
import sys
import time
import json
import datetime
import execjs
from urllib import urlencode
from mioji.common.class_common import Room
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
from mioji.common import parser_except

reload(sys)
sys.setdefaultencoding('utf-8')
size_pat = re.compile(r'\d+-?\d+', re.S)
base_url = 'http://hotels.ctrip.com/international/Tool/AjaxHotelRoomInfoDetailPart.aspx?'
headers = {
    'Host': 'hotels.ctrip.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Accept': '*/*',  # 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    'Connection': 'keep-alive',
}


def clean_data(st):
    st = re.sub(r'<(.*?)>', '', st)
    return st.replace('\n', '').strip().encode('utf-8')


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


class ctripHotelSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'ctripHotel'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertHotel_room4
        'room': {'version': 'InsertHotel_room3'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'ctripHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(ctripHotelSpider, self).__init__(task)
        self.no_repeat_dict = {'HotelRoomData': {'subRoomList': [], 'roomList': []}}
        self.callback_req = ''
        self.callback_param = ''
        self.headers = headers
        self.RemainingSegmentationNo_list = []
        if task:
            self.process_info()

    def process_info(self):
        cid = self.task.ticket_info.get('cid', None)
        city_id, hotel_id, check_in_form, check_out_form = '', '', '', ''
        try:
            task_infos = self.task.content.split('&')
            hotel_id, stay_nights, check_in = task_infos[0], task_infos[1], task_infos[2]

            check_out_form = str(datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), \
                                                   int(check_in[6:])) + datetime.timedelta(days=int(stay_nights)))[:10]
            check_in_form = check_in[0:4] + '-' + check_in[4:6] + '-' + check_in[6:]
        except Exception, e:
            parser_except.ParserException(parser_except.TASK_ERROR, 'ctripHotel :: 任务错误')
        print self.task.ticket_info
        # ctrip 有点奇葩  room_num 是成人的数目， 暂时不支持children
        room_num = str(self.task.ticket_info['room_info'][0].get('occ', 2))  # str(2)  # default
        # guest_num = str(self.task.ticket_info.get('occ', 2))  # str(2)
        child_num = str(self.task.ticket_info['room_info'][0].get('occ', 2))  # str(2)
        self.user_datas['infomation'] = (city_id, hotel_id, check_in_form, check_out_form, \
                                         room_num, child_num, cid)
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

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_room)
        def second_request():
            param = self.get_param()
            # second_url = base_url + urlencode(self.get_param())
            self.user_datas['t'] = str(int(time.time() * 1000))
            param['t'] = self.user_datas['t']
            second_url = base_url + urlencode(param)
            return {'req': {'url': second_url, 'headers': self.headers},
                    'data': {'content_type': 'json'},
                    'user_extra': 'second_request',
                    }
        return [first_request, second_request]

    def first_user_handler(self, req, data):
        """
        解析页面获取eleven
        :param req:
        :param data:
        :return:
        """
        city_id, hotel_id, check_in_form, check_out_form, room_num, child_num, cid = self.user_datas['infomation']
        eleven = ''

        try:
            ph_runtime = execjs.get('PhantomJS')
        except:
            raise parser_except.ParserException(97, '未配置PhantomJS')
        try:
            do = 'var Image = function(){}; var window = {}; window.document = {}; ' \
                 'var document = window.document; ' \
                 'window.navigator = ' \
                 '{"appCodeName":"Mozilla", "appName":"Netscape", "language":"zh-CN", "platform":"Win"}; ' \
                 'var navigator = window.navigator; window.location = {}; ' \
                 'window.location.href = "http://hotels.ctrip.com/hotel/hotelid.html"; ' \
                 'var location = window.location; '
            do = do.replace('hotelid', self.user_datas['infomation'][1])
            pat = re.compile(r'new Function\(\'return "\' \+ (.+) \+ \'\";\'\)')
            pat = re.compile(r'new Function\(\'return "\' \+ (.+) \+ \'\";\'\)')
            # pat2 = re.compile(r'new Function\(\'return "\' \+ .+ \+ \'\";\'\)')
            pat2 = re.compile(r'new Function\(\'return "\' \+ .+ \+ \'\";\'\)')
            pat3 = re.compile(r'/international/.+?\.html')
            jscontent = data
            jscontent = jscontent.replace('eval(', '')[:-1]  # 加密的javaScript
            runjs = ph_runtime.eval(jscontent)
            # print runjs
            eleven_str = pat.findall(runjs)
            need_to_replace = pat2.findall(runjs)
            url_str = '\"http://hotels.ctrip.com/{0}.html\"'.format(hotel_id)
            # url_str = '\"' + 'http://hotels.ctrip.com' + pat3.findall(runjs)[0] + '\"'
            self.headers.setdefault('Referer', url_str.replace('"', "").replace(r'com/', r'com/international/'))
            replace_str = self.callback_param + '(' + need_to_replace[0] + ')'  # 需要替代的javaScript
            # print replace_str
            js = runjs.replace(replace_str, 'return ' + eleven_str[0])  # 原本调用函数返回，这个直接把eleven参数返回
            # print js
            js = do + js
            # js = js.replace(r'window.location.href', url_str).replace('document',
            #                                                           '\"xyz\"')  # 更改href参数，然后替代nodejs不支持的document参数
            js = js.replace(r'!!window.Script', 'false').replace(';!function()',
                                                                 'function run()')  # 先替代nodejs不支持的window参数，然后更改function的名称
            js = js[:-3]  # 删除js的自调用
            # print js
            # print '(' * 100
            eleven = ph_runtime.compile(js).call('run')
            if eleven == None:
                parser_except.ParserException(parser_except.PROXY_INVALID, 'ctripHotel :: 获取eleven失败')
        except Exception as e:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, 'ctripHotel :: 获取eleven失败')
        print eleven, '*' * 100
        self.user_datas['eleven'] = eleven

    def get_param(self):
        """
        获取 请求参数  data
        """
        city_id, hotel_id, check_in_form, check_out_form, room_num, child_num, cid = self.user_datas['infomation']
        print self.user_datas
        data = {
            'city': str(city_id),
            'hotel': str(hotel_id),  # '998369',
            'EDM': 'F',
            'urlReferedForOtherSeo': 'False',
            'Pkg': 'F',
            'StartDate': str(check_in_form),
            'DepDate': str(check_out_form),
            'RoomNum': str(room_num),
            'IsNoLocalRoomHotel': 'T',
            'UserUnicode': '',
            'requestTravelMoney': 'F',
            'abt': 'B',
            'promotionid': '',
            'childNum': str(child_num),
            'FixSubHotel': 'F',
            'allianceid': '',
            'sid': '',
            'timestamp': '0',
            'guid': '',
            'pid': '',
            'sd': '',
            'userCouponPromoId': '',
            'Coupons': '',
            'isNeedAddInfo': 'true',
            'PageLoad': 'true',
            'eleven': self.user_datas.get('eleven', ''),  # 每次调用获取eleven的参数都会更新eleven
        }
        return data

    def cache_check(self, req, data):
        '''
        该回调可用于检测缓存是否有效\正确。
        :return: False 框架会重新走数据请求
        '''
        return Spider.cache_check(self, req, data)

    def clean_data(self, st):
        st = re.sub(r'<(.*?)>', '', st)
        return st.replace('\n', '').strip().encode('utf-8')

    # def check_all_result(self):
    #     super(ctripHotelSpider, self).check_all_result()
    #
    #     print self.RemainingSegmentationNo_list, 'RemainingSegmentationNo_list'
    #     # if self.user_datas.get()
    #     if self.user_datas.get('SegmentationCount', 0) == 0:
    #         self.code = 29
    #     elif len(self.RemainingSegmentationNo_list) == self.user_datas.get('SegmentationCount', -1):
    #         self.code = 0
    #     elif len(self.RemainingSegmentationNo_list):
    #         self.code = 95

    def parse_room(self, req, data):
        city_id, hotel_id, check_in_form, check_out_form, room_num, child_num, cid = self.user_datas['infomation']
        rooms = []
        if data['LoadStatus'] != 'Success':
            raise parser_except.ParserException(23, '代理封禁')

        if data['ResultCode'] in (2, 5):
            # 2 表示loading
            # 5 表示酒店没有可预订房间
            return []

        con_dict = data.get('HotelRoomData', {})
        if not con_dict:
            return []
        room_type_list = {}
        for rl in con_dict['roomList']:
            print rl['id']
            room_type_list[rl['id']] = rl
        all_p = con_dict['subRoomList']
        lll = len(all_p)
        print lll, "F<lll>"
        for each in all_p:
            if not each['canBook']:
                continue
            room = Room()
            room.hotel_name = re.sub('(\([\s\S]+?\))', '', con_dict['name']).encode('utf8')
            room.source = 'ctrip'.encode('utf-8')
            room.check_in = check_in_form.encode('utf-8')
            room.check_out = check_out_form.encode('utf-8')
            room.city = cid
            # room.city = City[city_code]['city_name_zh'].encode('utf-8')
            room.source_hotelid = con_dict['id']
            room.real_source = 'ctrip'.encode('utf-8')
            # room.room_type = each['name']
            room_type_id = each['baseRoomId']
            room_type = room_type_list[room_type_id]
            try:
                room.room_type = room_type['name']
            except:
                pass
            try:
                facilityTypes = room_type['roomInfoDetails']['FacilitiesOutput']['FacilityTypes']
                fac_list = []
                # print facilityTypes, 'facilityTypes'
                for ft in facilityTypes:
                    fac_list.append(ft['TypeName'] + ": " + " ".join(ft['FacilityName']))
                room.room_desc = "||".join(self.clean_data(fl) for fl in fac_list)
                # print room.room_desc
            except Exception, e:
                # print e
                pass
            # print 2323
            # img_urls
            try:
                img_urls = ''
                img_urls = '|'.join(room_type['roomInfoDetails']['images'])
            except Exception, e:
                img_urls = ''
            # print img_urls.encode('utf-8'), 'img_urls'
            room_details = ''.join(room_type['roomInfoDetails']['details']).encode('utf-8')
            try:
                # print room_details
                size = re.findall(r'(\d+?\.?\d+?)平方米', room_details)[0]
                room.size = size
                # print room.size, 'dsadsadsadsadsadsadsadsadsa'
                # room.size = size_pat.findall(size)[0]
            except Exception, e:
                # print e
                room.size = -1

            try:
                floor = re.findall(r'(\d+?)层', room_details)[0]
                # print floor
                room.floor = floor
                # floor = room_type['roomInfoDetails']['details'][2]
                # room.floor = size_pat.findall(floor)[0]
            except Exception, e:
                room.floor = -1
            try:
                if each['payment'] == 'PP' or each['payment'] == 'PH':
                    room.pay_method = '在线支付'.encode('utf-8')
                elif each['payment'] == 'FG':
                    room.pay_method = '支付方式'.encode('utf-8')
                else:
                    room.pay_method = '到店支付'.encode('utf-8')
            except:
                pass
            try:
                room.source_roomid = room_type_id
            except:
                pass

            try:
                room.price = each['price']['TotalPrice']
                # if each['showVIPPrice'] == 'True':
                #     room.price = each['price']['TotalPrice']
                # elif each['showVIPPrice'] == 'False': # 会员价格不显示，需要修改
                #     room.price = each['price']['TotalPrice']
            except:
                pass
            try:
                room.currency = "CNY"
            except:
                pass
            try:
                room.occupancy = each['maxPerson']
            except:
                pass
            try:
                room.return_rule = room.change_rule = clean_data(each['policyInfo']['info']).encode('utf-8')
                # print room.return_rule
            except:
                pass
            try:
                if each['canCancel']:
                    room.is_cancel_free = "NULL".encode('utf-8')
                else:
                    room.is_cancel_free = "No".encode('utf-8')
            except:
                pass
            try:
                room.rest = each['last']
                # with open('each.json', 'w') as f:
                #     json.dumps(each,f)
                if room.rest == 0:
                    # 表示票充足
                    room.rest = 9
                    if each['status'] == 'N':
                        # 表示票已订完
                        room.rest = 0
            except:
                pass
            try:

                bed_type = each['facilityInfo']['bed']
                # print bed_type.encode('utf-8'), 'bed_type'
                if bed_type != '':
                    room.bed_type = bed_type.encode('utf-8')
                    # print room.bed_type, '21212121212121'*50
            except Exception, e:
                # print 33
                # traceback.print_exc()
                # print str(e), '12', 'ds'
                pass
            try:
                breakfast_info = each['breakfast']
                if '免费' in breakfast_info and '早' in breakfast_info:
                    room.has_breakfast = 'Yes'.encode('utf-8')
                    room.is_breakfast_free = 'Yes'.encode('utf-8')
                elif '无早' in breakfast_info:
                    room.has_breakfast = 'No'.encode('utf-8')
                else:
                    room.has_breakfast = "NULL"
            except:
                pass
            try:
                extra = {}
                extra['breakfast'] = breakfast_info
                extra['payment'] = room.pay_method
                extra['return_rule'] = room.return_rule
                extra['occ_des'] = "每间最多入住{}人".format(room.occupancy)
                others_info = {
                    "extra": extra,
                    'img_urls': img_urls.encode('utf-8')
                }
                room.others_info = json.dumps(others_info)
            except:
                pass
            # print room.others_info
            roomtuple = (str(room.hotel_name), str(room.city), str(room.source), \
                         str(room.source_hotelid), str(room.source_roomid), \
                         str(room.real_source), str(room.room_type), int(room.occupancy), \
                         str(room.bed_type), float(room.size), int(room.floor), str(room.check_in), \
                         str(room.check_out), int(room.rest), float(room.price), float(room.tax), \
                         str(room.currency), str(room.pay_method), str(room.is_extrabed), str(room.is_extrabed_free), \
                         str(room.has_breakfast), str(room.is_breakfast_free), \
                         str(room.is_cancel_free), str(room.extrabed_rule), str(room.return_rule),
                         str(room.change_rule), \
                         str(room.room_desc), str(room.others_info), str(room.guest_info))
            rooms.append(roomtuple)

        return rooms


if __name__ == "__main__":
    import httplib

    httplib.HTTPConnection.debuglevel = 1
    httplib.HTTPSConnection.debuglevel = 1
    task1 = Task()
    # task1.content = 'PAR&375666&1&20150328&5&2&23_24_2|43_0.5'
    # task1.content = 'PAR&37566&1&20150820'
    # task1.content = 'PAR&2157992&1&20160616'
    task1.content = '994990&1&20171213'
    spider = ctripHotelSpider(task1)
    result = spider.crawl()
    # result = spider.result
    print result, spider.result
    # for ta in task_list:
    #     task1.content = ta
    #     task1.ticket_info = {'cid': 1, 'occ': 3}
    #     spider = ctripHotelSpider(task1)
    #     result1 = spider.crawl()
    #     with open('result1.json','w+') as f:
    #         json.dumps(result1, f)
    #     print len(spider.result)
    # print len(spider.result['room'])


    """
    http://hotels.ctrip.com/international/Tool/AjaxHotelRoomInfoDetailPart.aspx?FixSubHotel=F&pid=&UserUnicode=&guid=&RoomNum=2&city=192&requestTravelMoney=F&eleven=4e77e1539738836f6e54477ea72d7a7035130f187da29abeb254f8e568367e07&childNum=2&abt=B&sid=&Coupons=&promotionid=&StartDate=2017-07-20&timestamp=0&hotel=2157992&Pkg=F&IsNoLocalRoomHotel=T&userCouponPromoId=&EDM=F&urlReferedForOtherSeo=False&allianceid=&DepDate=2017-07-21&sd= ]
    http://hotels.ctrip.com/international/Tool/AjaxHotelRoomInfoDetailPart.aspx?city=1229&hotel=998603&EDM=F&urlReferedForOtherSeo=False&Pkg=F&StartDate=2017-07-20&DepDate=2017-07-21&RoomNum=2&IsNoLocalRoomHotel=T&UserUnicode=&requestTravelMoney=F&abt=B&promotionid=&t=1492400427684&childNum=2&FixSubHotel=F&allianceid=&sid=&timestamp=0&guid=&pid=&sd=&userCouponPromoId=&Coupons=&SegmentationNo=1,3&SegmentationRPH=4017041711000183831&t2=1492400429731&eleven=9d44575be06c4ffc034074d11049abc90cbb1badb80c5e62095ac7aa34a1e539
    """

    """
    http://hotels.ctrip.com/international/Tool/AjaxHotelRoomInfoDetailPart.aspx?city=1229&hotel=998603&EDM=F&urlReferedForOtherSeo=False&Pkg=F&StartDate=2017-07-20&DepDate=2017-07-21&RoomNum=2&IsNoLocalRoomHotel=T&UserUnicode=&requestTravelMoney=F&abt=B&promotionid=&t=1492410112793&childNum=2&FixSubHotel=F&allianceid=&sid=&userCouponPromoId=&Coupons=&SegmentationNo=2,3&SegmentationRPH=3917041714000094921&t2=1492410118024&eleven=108e407c01818f59534234516be21768cf2477caa823a90de121b71bbfa26381
    http://hotels.ctrip.com/international/Tool/AjaxHotelRoomInfoDetailPart.aspx?FixSubHotel=F&pid=&UserUnicode=&guid=&RoomNum=2&city=192&requestTravelMoney=F&eleven=8300c08792da406e8615a0fe630eb824f8642ecc784059bf5a151f65ac15bc53&childNum=2&abt=B&sid=&Coupons=&promotionid=&StartDate=2017-07-20&timestamp=0&hotel=2157992&Pkg=F&IsNoLocalRoomHotel=T&userCouponPromoId=&EDM=F&urlReferedForOtherSeo=False&allianceid=&DepDate=2017-07-21&sd=
    """
