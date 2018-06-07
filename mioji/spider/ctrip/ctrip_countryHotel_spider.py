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
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.task_info import Task
from mioji.common import parser_except
from mioji.common.func_log import current_log_tag
from mioji.common.logger import logger
from lxml import html
from collections import defaultdict
from urlparse import urljoin
import traceback
from mioji.common.parser_except import PARSE_ERROR
from mioji.models.city_models import get_suggest_city
reload(sys)
sys.setdefaultencoding('utf-8')


size_pat = re.compile(r'\d+-?\d+', re.S)
#base_url = 'http://hotels.ctrip.com/international/Tool/AjaxHotelRoomInfoDetailPart.aspx?'
base_url = 'http://hotels.ctrip.com/Domestic/tool/AjaxHote1RoomListForDetai1.aspx?'
hotel_url = "http://hotels.ctrip.com/hotel/{0}.html?isFull=F"
headers = {
    'Host': 'hotels.ctrip.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
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
    source_type = 'ctripcnHotel'
    targets = {
        'room': {'version': 'InsertHotel_room3'},
    }
    old_spider_tag = {
        'ctripcnHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(ctripHotelSpider, self).__init__(task)
        self.no_repeat_dict = {'HotelRoomData': {'subRoomList': [], 'roomList': []}}
        self.callback_req = ''
        self.callback_param = ''
        self.headers = headers
        self.RemainingSegmentationNo_list = []

    def process_content_info(self):
        taskcontent = self.task.content
        self.city_id, self.hotel_id, check_in_form, check_out_form = '', '', '', ''
        try:
            taskcontent = taskcontent.encode('utf-8')
            task_infos = taskcontent.split('&')
            self.city_id, self.hotel_id, stay_nights, check_in = task_infos[0], \
                                                                  task_infos[1], task_infos[2], task_infos[3]                           
            check_out_form = str(datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), \
                                                   int(check_in[6:])) + datetime.timedelta(days=int(stay_nights)))[:10]
            check_in_form = check_in[0:4] + '-' + check_in[4:6] + '-' + check_in[6:]
            # self.hotel_id = hotel_id
            self_p = get_suggest_city('ctripcn', str(self.city_id)).split('|')
            city_id = self_p[5]
        except Exception, e:
            parser_except.ParserException(parser_except.TASK_ERROR, 'ctripHotel :: 任务错误')
        return self.process_info(city_id, self.hotel_id, check_in_form, check_out_form)

    def process_info(self,city_id,hotel_id,check_in_form,check_out_form):
        cid = self.task.ticket_info.get('cid', None)
        # ctrip 有点奇葩  room_num 是成人的数目， 暂时不支持children
        room_num = str(self.task.ticket_info.get('occ', 2))  # str(2)  # default
        # guest_num = str(self.task.ticket_info.get('occ', 2))  # str(2)
        child_num = str(self.task.ticket_info.get('occ', 2))  # str(2)
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
        callback_req = "http://hotels.ctrip.com/domestic/cas/oceanball?callback=%s&" % (
            str(call_back))
        return callback_req

    def targets_request(self):
        call_back_req = self.process_content_info()
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_request():
            """
                获取 eleven
            """
            return {
                'req': {'url': call_back_req, 'headers': self.headers, 'params': {'_': str(int(time.time() * 1000))}},
                'data': {'content_type': 'text'},
                'user_handler': [self.first_user_handler]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['room'])
        def second_request():
            param = self.get_param()
            second_url = base_url + urlencode(param)
            return {'req': {'url': second_url, 'headers': self.headers},
                    'data': {'content_type': 'json'},
                    'user_extra': 'second_request',
                    'user_handler': [self.hotel_handler]
                    }

        @request(retry_count=5,proxy_type=PROXY_REQ)
        def get_HotelName():
            req_hotel_url = hotel_url.format(self.hotel_id)
            return {
                'req':{'url':req_hotel_url,'headers':self.headers},
                'data':{'content_type':'html'},
                'user_handler':[self.process_hotelname]
            }
        yield first_request
        yield get_HotelName
        yield second_request

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['room'])
        def get_next():
            """
                获取剩下的部分
            """
            param = self.get_param()
            del param['isNeedAddInfo']
            del param['PageLoad']
            del param['guid']
            del param['timestamp']
            del param['pid']
            # del param['sd']
            SegmentationRPH = self.user_datas.get('SegmentationRPH', '')
            SegmentationNo = self.user_datas.get('SegmentationNo', '')
            param['SegmentationRPH'] = SegmentationRPH
            # param['RemainingSegmentationNo'] = RemainingSegmentationNo
            param['SegmentationNo'] = SegmentationNo
            param['t'] = self.user_datas['t']
            param['t2'] = str(int(time.time() * 1000))
            next_url = base_url + urlencode(param)
            return {'req': {'url': next_url, 'headers': self.headers,
                            },
                    'data': {'content_type': 'json'},
                    'user_handler': [self.hotel_handler],
                    'user_extra': 'third_request'
                    }

        SegmentationCount = self.user_datas.get('SegmentationCount', 1)
        print SegmentationCount, '*' * 100
        for i in xrange(1, SegmentationCount):
            if len(self.RemainingSegmentationNo_list) >= (i + 1):
                break
            for j in xrange(10):
                yield first_request
                yield get_next
                if len(self.RemainingSegmentationNo_list) >= (i + 1):
                    break

    def process_hotelname(self,req,data):
        root = data
        hotel_name = root.xpath('//h2[@class="cn_n"]/text()')[0].strip()
        hotel_name_en = re.search(r'\(([a-zA-z ]+)\)', hotel_name)
        hotel_name_cn = re.search(u'[\u4e00-\u9fa5]+', hotel_name)
        if hotel_name_cn:
            self.hotel_name = hotel_name_cn.group()
        else:
            self.hotel_name = hotel_name_en.group(1)


    def hotel_handler(self, req, data):
        try:
            self.user_datas['hasRoom'] = data['HasRoom']
            print type(self.user_datas['hasRoom']),self.user_datas['hasRoom']
            self.user_datas['isfullhouse'] = data['isFullHouse']
            self.user_datas['bookable'] = data['bookable']
            print type(self.user_datas['bookable']),data['bookable']
            html_content = data['html']
        except:
            logger.debug(current_log_tag()+'[解析错误]')
            print traceback.format_exc()
            raise parser_except.PARSE_ERROR

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
            pat = re.compile(r'new Function\(\'return "\' \+ (.+) \+ \'\";\'\)')
            pat2 = re.compile(r'new Function\(\'return "\' \+ .+ \+ \'\";\'\)')
            pat3 = re.compile(r'/international/.+?\.html')
            jscontent = data
            jscontent = jscontent.replace('eval(', '')[:-1]  # 加密的javaScript
            runjs = ph_runtime.eval(jscontent)
            # print runjs
            eleven_str = pat.findall(runjs)
            need_to_replace = pat2.findall(runjs)
            print "elevent_str,nedd_to_replace:",eleven_str,need_to_replace
            url_str = '\"http://hotels.ctrip.com/{0}.html\"'.format(hotel_id)
            self.headers.setdefault('Referer', url_str.replace('"', "").replace(r'com/', r'com/international/'))
            replace_str = self.callback_param + '(' + need_to_replace[0] + ')'  # 需要替代的javaScript
            # print replace_str
            js = runjs.replace(replace_str, 'return ' + eleven_str[0])  # 原本调用函数返回，这个直接把eleven参数返回
            # print js
            js = js.replace(r'window.location.href', url_str).replace('document',
                                                                      '\"xyz\"')  # 更改href参数，然后替代nodejs不支持的document参数
            js = js.replace(r'!!window.Script', 'false').replace(';!function()',
                                                             'function run()')  # 先替代nodejs不支持的window参数，然后更改function的名称
            js = js[:-3]  # 删除js的自调用
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
            'psid':'',
            'city': str(city_id),
            'hotel': str(hotel_id),  # '998369',
            'MasterHotelID': str(hotel_id),
            'EDM': 'F',
            'contrast':'0',
            'IsDecoupleSpotHotelAndGroup': 'F',
            'roomId':'',
            'IncludeRoom':'',
            'startDate': str(check_in_form),
            'depDate': str(check_out_form),
            'showspothotel':'T',
            'supplier':'',
            'RequestTravelMoney': 'F',
            'IsFlash':'F',
            'hsids': '',
            'IsJustConfirm':'',
            'contyped':'0',
            'priceInfo':'-1',
            'equip':'',
            'filter':'',
            'productcode':'',
            'couponList':'',
            "abForHuaZhu":'',
            'defaultLoad':'T',
            'TmFromList':'F',
            'eleven': self.user_datas.get('eleven', ''),  # 每次调用获取eleven的参数都会更新eleven
            'callback':self.callback_param,
            '_':str(int(time.time()*1000))
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

    def check_all_result(self):
        super(ctripHotelSpider, self).check_all_result()
        if not self.user_datas.get('hasRoom',False):
            self.code = 29
        elif self.user_datas.get('CanBookRoomNum',0):
            self.code = 0

    def parse_room(self, req, data):
        city_id, hotel_id, check_in_form, check_out_form, room_num, child_num, cid = self.user_datas['infomation']
        rooms = []
        if not self.user_datas['hasRoom'] or not data['bookable']:
            """
                hasRoom: 有房间，
                bookable:有能够预定的房间
            """
            return []

        html_content = data.get('html','')
        html_content = html_content.replace(u'&#39;',u'\'')
        root = html.fromstring(html_content)
        tr_list = root.xpath('//table/tr')[2:]
        img_list = defaultdict(str)
        room_type = defaultdict(str)
        room_size = defaultdict(int)
        for i,tr in enumerate(tr_list):
            room = Room()
            try:
                can_book = tr.xpath('./td/p[@class="base_box"]/span[@class="base_txtdiv"]')
                if can_book:
                    if re.search(r"'isfull':'([A-Za-z]+)'",can_book[0].attrib.get('data-params')).group(1) == u'T':
                        print "过滤掉预定完的房间"
                        continue
            except:
                print traceback.format_exc()
                logger.debug(current_log_tag()+'[房间没有订满]')
            try:
                remove_room = tr.xpath('./td[@class="col7"]/div[@class="book_type"]/span/a/@href')
                print "remove_room:",remove_room
                if remove_room:
                    continue
                remove_tr = tr.attrib.get('class')
                if u'clicked hidden' in remove_tr:
                    print "过滤掉clicked hidden"
                    continue
                remove_jorn = tr.xpath('./td/p[@class="base_box"]/span[@class="base_txtdiv"]')
                if remove_jorn:
                    if u'登录' in remove_jorn[0].attrib.get('data-params') and  tr.attrib.get('class'):
                        print "过滤掉需要登录才能预定的酒店"
                        continue
            except:
                print traceback.format_exc()
                logger.debug(current_log_tag()+"[属于该酒店下的房间]")
            if not tr.attrib.get('class',None) or tr.attrib.get('class',None) == 'last_room':
                try:
                    img_list[tr.attrib.get('brid')] = '|'.join([urljoin('http:',value) for key,value in tr.xpath('./td/a[@class="pic"]/img')[0].attrib.items() if key == 'src' or key =='_src'])
                    room.others_info = json.dumps({'img_urls':img_list[tr.attrib.get('brid')]})
                except:
                    try:
                        img_list[tr.attrib.get('brid')] = '|'.join([urljoin('http:', value) for key, value in
                                                                    tr.xpath('./td/a[@class="pic J_show_room_detail"]/img')[
                                                                        0].attrib.items() if
                                                                    key == 'src' or key == '_src'])
                        room.others_info = json.dumps({'img_urls': img_list[tr.attrib.get('brid')]})
                    except:
                        print traceback.format_exc()
                        logger.debug(current_log_tag()+'[解析基本房间图片失败]')

                try:
                    room_type[tr.attrib.get('brid')] = tr.xpath('./td/a[@class="room_unfold"]/text()')[0].strip()
                    room.room_type = room_type[tr.attrib.get('brid')]
                except:
                    try:
                        room_type[tr.attrib.get('brid')] = tr.xpath('./td/a[@class="room_unfold J_show_room_detail"]/text()')[0].strip()
                        room.room_type = room_type[tr.attrib.get('brid')]
                    except:
                        try:
                            room_type[tr.attrib.get('brid')] = \
                            tr.xpath('./td/a[@class="room_unfold"]/text()')[0].strip()
                            room.room_type = room_type[tr.attrib.get('brid')]
                        except:
                            logger.debug(current_log_tag()+"[解析房间类型失败]")
                            raise PARSE_ERROR
                print "房间数",i,"room_type",room.room_type
                try:
                    size = int(re.search(r'[\d]+',tr.xpath('./td/a[@class="room_unfold"]/p[@class="room_extend room_size"]')[0].text_content()).group(0))
                    room_size[tr.attrib.get('brid')] = size
                    room.size = room_size[tr.attrib.get('brid')]
                except:
                    try:
                        size = int(re.search(r'[\d]+',
                                             tr.xpath('./td/a[@class="room_unfold J_show_room_detail"]/p[@class="room_extend room_size"]')[
                                                 0].text_content()).group(0))
                        room_size[tr.attrib.get('brid')] = size
                        room.size = room_size[tr.attrib.get('brid')]
                    except:
                        room_size[tr.attrib.get('brid')] = -1
                        print traceback.format_exc()
                        logger.debug(current_log_tag()+'[没有解析到房间面积]')
            else:
                room.others_info = json.dumps({'img_urls':img_list[tr.attrib.get('brid')]})
                room.room_type = room_type[tr.attrib.get('brid')]
                room.size = room_size[tr.attrib.get('brid')]
            try:
                return_rule = tr.xpath('./td[@class="col_policy"]/span[@class="room_policy"]/@data-params')
                if return_rule:
                    room.return_rule = eval(return_rule[0]).get('options',{}).get('content',{}).get('txt',None)
            except:
                print traceback.format_exc()
                logger.debug(current_log_tag()+"[解析退订政策出错]")
            try:
                room.bed_type = tr.xpath('./td[@class="col3"]/text()')[0]
                print "房间数：",i,"bed_type",room.bed_type
                params = tr.xpath('./td[@class="col7"]/div[@class="book_type"]/a')[0].attrib
                if params.get('tracevalue',None):
                    room.source_hotelid = hotel_id
                    room.source_roomid = eval(params.get('tracevalue',{})).get('roomid')
                    room.check_in = check_in_form
                    room.check_out = check_out_form
                    room.city = self.city_id
                    room.price = float(params.get('data-price')) * int(room_num)
                    pay_method = params.get('data-order').split(',')[4]
                    if u'PP' in pay_method or u'PH' in pay_method:
                        room.pay_method = '预付'
                    else:
                        room.pay_method = '现付'
                    print "房间数：",i,"roomid:",room.source_roomid
                else:
                    pass
            except:
                print traceback.format_exc()
                logger.debug(current_log_tag()+"[解析房间关键信息出现错误]")
            try:
                room.occupancy = int(re.search(r'[\d]+', tr.xpath(
                    './td[@class="col_person"]/span[@class="htl_room_person02"]/@title')[0]).group(0))
            except:
                try:
                    room.occupancy = int(re.search(r'[\d]+', tr.xpath(
                        './td[@class="col_person"]/span[@class="htl_room_person03"]/@title')[0]).group(0))
                except:
                    try:
                        room.occupancy = int(re.search(r'[\d]+', tr.xpath(
                            './td[@class="col_person"]/span[@class="htl_room_persons"]/@title')[0]).group(0))
                    except:
                        try:
                            room.occupancy = int(re.search(r'[\d]+', tr.xpath(
                                './td[@class="col_person"]/span[@class="htl_room_person01"]/@title')[0]).group(0))
                        except:
                            print traceback.format_exc()
                            logger.debug(current_log_tag()+"[解析最大入住人数出错]")
            print "房间数：",i,"occupancy",room.occupancy

            try:
                try:
                    breakfast = tr.xpath('./td[@class="text_green col4"]/text()')[0]
                except:
                    try:
                        breakfast = tr.xpath('./td[@class="col4"]/text()')[0]
                    except:
                        pass
                if u'无早' in breakfast:
                    room.is_breakfast_free = 'No'
                else:
                    room.has_breakfast = 'Yes'
                    room.is_breakfast_free = 'Yes'
            except:
                print traceback.format_exc()
                logger.debug(current_log_tag()+"[没有解析到早餐参数]")
            try:
                cancel = tr.xpath('./td[@class="col_policy"]/span[@class="room_policy"]')[0].text
                if u'不可取消' in cancel:
                    room.is_cancel_free = 'No'
                else:
                    room.is_cancel_free = 'Yes'
            except:
                logger.debug(current_log_tag()+"[没有解析到可取消参数]")
            try:
                extrabed = tr.xpath('./td[@class="child_name"]')[0].attrib.get('data-baseRoomInfo')
                if u'可加床' in extrabed:
                    room.is_extrabed = 'Yes'
            except:
                logger.debug(current_log_tag()+"[没有解析到可加床参数]")
            try:
                last_room = tr.xpath('./td/div[@class="book_type"]/div[@class="hotel_room_last"]/text()')[0]
                if last_room:
                    room.rest = int(re.search(r'(\d+)',last_room).group(1))
                else:
                    room.rest = -1
            except:
                logger.debug(current_log_tag()+'[没有解析到剩余房间]')
            room.currency = 'CNY'
            room.source = 'ctripcn'
            room.real_source = 'ctripcn'
            room.hotel_url = hotel_url.format(hotel_id)
            room.hotel_name = self.hotel_name
            if room.source_roomid != 'NULL' and room.occupancy != -1:
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
    from mioji.common.utils import simple_get_socks_proxy,simple_get_http_proxy
    from mioji.common import spider
    spider.get_proxy = simple_get_socks_proxy
    task1 = Task()
    # task1.content = '58&436835&3&20170930'
    task1.content = '20078&926224&2&20171118'
    task1.ticket_info['occ'] = 2
    # task1.ticket_info = {
    #     'hotel_url': 'http://hotels.ctrip.com/international/688406.html?isfull=F&cbn=224&ecp=1122&ep=58364316&sd=F&ti=110106-60c2f7f2-cc95-4697-a4f6-6e8f2e2d83a4&pi=102102&tt=1502937211&NoShowSearchBox=T#ctm_ref=hi_0_0_0_0_lst_sr_1_df_ls_11_n_hi_0_0_0',
    #     'night':2,
    #     'checkin_date': '20170820'
    # }
    spider = ctripHotelSpider(task1)
    spider.crawl()
    result = spider.result['room']
    print result
 