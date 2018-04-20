#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
onetravel
'''

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re
import json
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.logger import logger
import time
import datetime
from mioji.common.class_common import Room
import execjs
from mioji.common.parser_except import ParserException

hd = {
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Host': 'm.elong.com',
    'DNT': '1',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
}


class ElongHotel(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'elongHotel'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        'room': {'version': 'InsertHotel_room3'},
    }

    # unable = True
    #   对应多个原爬虫
    old_spider_tag = {
        'elongHotel': {'required': ['room']}
    }

    def prepare_params(self):
        self.user_datas['code'] = ''
        taskcontent = self.task.content
        self.user_datas['cid'] = self.task.ticket_info.get('cid', None)
        info_list = taskcontent.split('&&')
        "ROM&&294945&&圣彼得无限酒店&&3023&&1&&20170705"
        city_name = info_list[0]
        self.user_datas['hotel_id'] = info_list[1]
        self.user_datas['hotel_name'] = info_list[2]
        regionid = info_list[3]
        nights = info_list[4]
        check_in_temp = info_list[5]
        self.user_datas['check_in'] = check_in_temp[:4] + '-' + check_in_temp[4:6] + '-' + check_in_temp[6:]
        check_out_temp = datetime.datetime(int(check_in_temp[:4]), int(check_in_temp[4:6]), int(check_in_temp[6:]))
        self.user_datas['check_out'] = str(check_out_temp + datetime.timedelta(days=int(nights)))[:10]
        hotel_id_temp = self.user_datas['hotel_id']
        room_num, adult_num, child_num = self.get_rooms_and_guests()
        self.user_datas['adult_num'] = adult_num
        if self.task.ticket_info.has_key('occ'):
            self.user_datas['adult_num'] = self.task.ticket_info['occ']
        cstr = 'IHotelSearch=RegionName=%E5%8D%8E%E6%B2%99%E5%8F%8A%E5%91%A8%E8%BE%B9&RegionId=178317&OutDate=' + \
               self.user_datas['check_out'] + '&InDate=' + self.user_datas['check_in'] + '&RoomPerson=' + str(
            room_num) + '%7C' + str(adult_num) + '%2B' + str(child_num) + '%2B&RegionNameAlpha=seoul(andvicinity)&;'
        # timesap = str(int(float(time.time()) * 1000))
        self.user_datas['url'] = 'http://m.elong.com/ihotel/{0}/?source_id={0}#detailTab'.format(
            self.user_datas['hotel_id'])
        self.user_datas['url_code'] = 'http://ihotel.elong.com/detail/scriptCode?hotelId={0}&_={1}'
        # self.user_datas['url1'] = 'http://ihotel.elong.com/isajax/Detail/roomList?hotelid={0}&secondNeedMapping=0&code={1}&_={2}'
        self.user_datas[
            'url1'] = 'http://m.elong.com/ihotel/detail/DetailRoomList/?hotelId={3}&inDate={0}&outDate={1}&roomPerson=1|{4}&code={2}'
        # url参数中 roomPerson=$(房间数)|$(人数)
        # hd['Cookie'] = cstr
        hd['Referer'] = self.user_datas['url']
        self.user_datas['hd'] = hd
        self.user_datas['cookie'] = cstr

    def targets_request(self):

        self.prepare_params()

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def pre_request():
            return {
                'req': {'url': self.user_datas['url'],
                        # self.user_datas['url_code'].format(self.user_datas['hotel_id'], str(int(float(time.time()) * 1000))),
                        'headers': self.user_datas['hd'],
                        'method': 'get'},
                'data': {'content_type': 'html'},
                'user_handler': [self.pre_handler]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def script_request():
            return {
                'req': {'url': self.user_datas['url_code'].format(self.user_datas['hotel_id'],
                                                                  str(int(float(time.time()) * 1000))),
                        # self.user_datas['url_code'].format(self.user_datas['hotel_id'], str(int(float(time.time()) * 1000))),
                        'headers': self.user_datas['hd'],
                        'method': 'get'},
                'data': {'content_type': 'json'},
                'user_handler': [self.script_handler]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_room)
        def pages_request():
            return {
                'req': {'url': self.user_datas['url1'].format(self.user_datas['check_in'],
                                                              self.user_datas['check_out'],
                                                              self.user_datas['code'],
                                                              self.user_datas['hotel_id'],
                                                              self.user_datas['adult_num'], ),
                        'headers': self.user_datas['hd'],
                        'method': 'get'},
                'data': {'content_type': self.user_data_convert},
                'id': 'prepare'
            }

        return [pre_request, pages_request]

    # def prepare_request(self, request_template):
    #     if request_template.get('id'):
    #         timestamp = str(int(float(time.time()) * 1000))
    #         code = self.user_datas['code']
    #         request_template['req']['url'] = self.user_datas['url1'].format(self.user_datas['hotel_id'], code, timestamp)

    def script_handler(self, req, data):
        try:
            ph_runtime = execjs.get('PhantomJS')
        except:
            raise ParserException(97, '未配置PhantomJS')
        final_js = """
                function c() {
                    try {
                        var d = %s;
                        if (null == d || "" === d || !d)return -99;
                        var a = decrypt(d), script = eval(h(a));
                        return script
                    } catch (e) {
                        return -99
                    }
                    function decrypt(dynamicScript) {
                        var key = "ihotel_js_key123", iv = "1234567890123456",
                            decipher = crypto.createDecipheriv("aes-128-cbc", key, iv),
                            decrypted = decipher.update(dynamicScript, "hex", "binary");
                        return decrypted += decipher["final"]("binary"), null != decrypted && "" !== decrypted && decrypted ? decrypted : ""
                    }

                    function h(script) {
                        return null == script || "" === script ? script : script.replace(/\)\^-1/gm, ")&-1")
                    }
                }
                """ % req["data"]
        fun = ph_runtime.compile(final_js)
        self.user_datas['code'] = fun.call('c')
        print self.user_datas['code']

    def pre_handler(self, req, data):
        # lxml //*[@id="tsdDetail"]
        try:
            value_str = data.xpath('//*[@id="tsdDetail"]/@value')[0]
        except:
            raise ParserException(ParserException.PROXY_INVALID, "elong:访问过快或者页面无酒店")
        try:
            ph_runtime = execjs.get('PhantomJS')
        except:
            raise ParserException(97, '未配置PhantomJS')
        # 此处js为完成location的设置
        js_func = ph_runtime.compile(
            '''
            var localContext = {
                "location": {
                    href: "http://m.elong.com",
                    hostname: "m.elong.com"
                },
                "history": "history",
                "document": {
                    createElement: function () {
                    }
                }
            };
            with (localContext) 
            {
                var a=%s;
                var b=a.replace(/\)\^-1/gm, ")&-1");
                var c=eval(b);
            }
            ''' % (
                repr(value_str),))
        try:
            check_code = str(js_func.eval('c'))
        except RuntimeError, e:
            logger.info('js获取错误，无法运行，主动重试')
            raise ParserException(ParserException.PROXY_INVALID, '获取js错误，主动重试')
        # 获得一个code
        hd['Referer'] = self.user_datas['url']
        self.user_datas['code'] = check_code


        # hd_temp = req['resp'].headers['Set-Cookie']
        # self.user_datas['hd']['Cookie'] = hd_temp.replace('path=/', '').replace('; ;', ';').replace(
        #     'domain=elong.com, ', '') \
        #                                       .replace('domain=ihotel.elong.com, ', '') + self.user_datas[
        #                                       'cookie'] + ' _xsrf=2|dc449d54|3920bbb5ea307072cbfd6dce39dce444|1493027114;' \
        #                                   + ' Esid=7bb958c5-7d60-46ef-ab2e-831e65aaaca4;'
        # val = data["data"]
        # 处理code参数
        # val = data.xpath('//input[@id="tsd"]/@value')[0]

    def user_data_convert(self, req, data):
        import json
        return json.loads(data, 'utf-8')

    def get_rooms_and_guests(self):
        info_list = self.task.content.split('&&')
        room_num = 1
        adult_num = 1
        child_num = 0

        try:
            if len(info_list) > 5:
                room_num = info_list[6]
                adult_num = info_list[5]
                age_list = info_list[7].replace('|', '_').split('_')
                for ele in age_list:
                    if int(ele) < 12:
                        child_num = child_num + 1
                    else:
                        adult_num = adult_num + 1

                adult_num = adult_num - 1
            else:
                pass
        except:
            room_num = 1
            adult_num = 1

        return room_num, adult_num, child_num

    def parse_room(self, req, data):
        room_list = []
        try:
            isneedmap = data.get('data', {}).get('isNeedRoomMapping')
            rooms_types = data.get('data', {}).get('roomList', {})
        except Exception, e:
            raise ParserException(ParserException.PROXY_INVALID, "elong:elong 访问过快或者页面无酒店")

        if isneedmap:
            for room_inf in rooms_types:
                room = Room()
                room_infos = room_inf['subRoomList']

                for room_info in room_infos:
                    try:
                        payType = room_info.get('payType', None)
                        if payType == 2:
                            room.pay_method = "到店支付".encode('utf-8')
                        if payType == 1:
                            room.pay_method = "在线支付".encode('utf-8')
                    except Exception, e:
                        pass

                    try:
                        room.occupancy = room_info.get('roomDesc', {}).get('maxPersonNum', self.user_datas['adult_num'])
                        if int(room.occupancy) == 0:
                            room.occupancy = self.user_datas['adult_num']

                    except Exception, e:
                        pass

                    room.occupancy = int(room.occupancy)

                    try:
                        room.source_roomid = room_info['roomId']
                    except Exception, e:
                        pass

                    try:
                        room.room_type = room_info.get("roomName", room.room_type)
                    except Exception, e:
                        pass

                    room_desc = room_info.get('roomDesc', {})
                    if room_desc:

                        try:
                            breakfast_info = room_desc.get('breakFast', u'\u4e0d\u542b\u65e9\u9910')
                            if breakfast_info != u'\u4e0d\u542b\u65e9\u9910':
                                room.has_breakfast = "Yes"
                                room.is_breakfast_free = "Yes"
                            else:
                                room.has_breakfast = "No"
                                room.is_breakfast_free = "No"

                            bed_types = room_desc.get('bedTypes', [])
                            room.bed_type = "||".join(bed_types) or "NULL"
                        except Exception, e:
                            pass

                    try:
                        joinRoomDesc = room_info.get('joinRoomDesc', "")
                        # print '~@#$'*20,joinRoomDesc
                        joinRoomDesc_ = re.sub(r'<.*?>', '', joinRoomDesc)
                        # print '&*&*'*20, joinRoomDesc_,type(joinRoomDesc_)
                        productDesc = room_info.get('productDesc', "")
                        # print '*&'*20,productDesc
                        productDesc_ = re.sub(r'<.*?>', '', productDesc)
                        room.room_desc = productDesc_ + joinRoomDesc_
                    except Exception, e:
                        pass

                    try:
                        room.rest = int(room_info.get('allotment', room.rest))
                    except Exception, e:
                        pass

                    try:
                        te = room.room_desc
                        if u'平方米' in te:
                            temp_size = ''
                            try:
                                temp_size = re.findall(u'面积 ?(\d+)', te)[0]
                                room.size = int(temp_size)
                            except:
                                pass

                            if temp_size == '':
                                try:
                                    temp_size = re.findall(u'面积 ?(\d+)', te)[0]
                                    room.size = int(temp_size)
                                except:
                                    pass

                            if temp_size == '':
                                try:
                                    temp_size = re.findall(u'(\d+.?\d*?) ?平方米', te)[0]
                                    room.size = int(temp_size)
                                except:
                                    pass
                    except Exception, e:
                        pass

                    try:
                        room.price = float(room_info.get('totalPrice'))
                        if int(room.price) <= 0:
                            continue
                    except Exception, e:
                        continue

                    try:
                        free_cancel_flag = room_info.get("cancellationType", {}).get('type', 0)
                        if free_cancel_flag == 0:
                            room.is_cancel_free = "No" # 不可取消
                        elif free_cancel_flag == 1:
                            room.is_cancel_free = "NULL" # 限时免费取消
                        elif free_cancel_flag == 2:
                            room.is_cancel_free = "NULL" # 收费取消
                    except Exception, e:
                        continue

                    room.return_rule = room_info.get('cancellationShowDesc', "").replace("<br>", '')
                    room.change_rule = ''

                    room.source_hotelid = self.user_datas['hotel_id']
                    room.hotel_name = self.user_datas['hotel_name']
                    room.city = self.user_datas['cid']
                    room.check_in = self.user_datas['check_in']
                    room.check_out = self.user_datas['check_out']
                    room.source = 'elong'
                    room.currency = 'CNY'
                    room.real_source = 'elong'
                    other_info = dict()
                    other_info['extra'] = {}
                    other_info['extra']['breakfast'] = breakfast_info
                    other_info['extra']['payment'] = room.pay_method
                    other_info['extra']['return_rule'] = room.return_rule
                    other_info['extra']['occ_des'] = "每间最多可入住{}人，如需加床或者带小孩儿，可能会收取费用。".format(room.occupancy)
                    room.others_info = json.dumps(other_info)
                    # print type(room.occupancy)
                    room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                                  room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                                  room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                                  room.rest, room.price, room.tax, room.currency, room.pay_method, \
                                  room.is_extrabed, room.is_extrabed_free, room.has_breakfast, \
                                  room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, \
                                  room.return_rule, room.change_rule, room.room_desc, \
                                  room.others_info, room.guest_info)
                    room_list.append(room_tuple)

            return room_list
        else:
            for room_inf in rooms_types:
                room = Room()
                room_infos = room_inf['providerRoomInfo']

                for room_info in room_infos:
                    try:
                        payType = room_info.get('payType', None)
                        if payType == 2:
                            room.pay_method = "到店支付".encode('utf-8')
                        if payType == 1:
                            room.pay_method = "在线支付".encode('utf-8')
                    except Exception, e:
                        pass

                    try:
                        room.occupancy = room_info.get('roomDesc', {}).get('maxPersonNum', self.user_datas['adult_num'])
                        if int(room.occupancy) == 0:
                            room.occupancy = self.user_datas['adult_num']

                    except Exception, e:
                        pass

                    room.occupancy = int(room.occupancy)

                    try:
                        room.source_roomid = room_info['roomId']
                    except Exception, e:
                        pass

                    try:
                        room.room_type = room_info.get("roomName", room.room_type)
                    except Exception, e:
                        pass

                    room_desc = room_info.get('roomDesc', {})
                    if room_desc:

                        try:
                            breakfast_info = room_desc.get('breakFast', u'\u4e0d\u542b\u65e9\u9910')
                            if breakfast_info != u'\u4e0d\u542b\u65e9\u9910':
                                room.has_breakfast = "Yes"
                                room.is_breakfast_free = "Yes"
                            else:
                                room.has_breakfast = "No"
                                room.is_breakfast_free = "No"

                            bed_types = room_desc.get('bedTypes', [])
                            room.bed_type = "||".join(bed_types) or "NULL"
                        except Exception, e:
                            pass

                    try:
                        joinRoomDesc = room_info.get('joinRoomDesc', "")
                        # print '~@#$'*20,joinRoomDesc
                        joinRoomDesc_ = re.sub(r'<.*?>', '', joinRoomDesc)
                        # print '&*&*'*20, joinRoomDesc_,type(joinRoomDesc_)
                        productDesc = room_info.get('productDesc', "")
                        # print '*&'*20,productDesc
                        productDesc_ = re.sub(r'<.*?>', '', productDesc)
                        room.room_desc = productDesc_ + joinRoomDesc_
                    except Exception, e:
                        pass

                    try:
                        room.rest = int(room_info.get('allotment', room.rest))
                    except Exception, e:
                        pass

                    try:
                        te = room.room_desc
                        if u'平方米' in te:
                            temp_size = ''
                            try:
                                temp_size = re.findall(u'面积 ?(\d+)', te)[0]
                                room.size = int(temp_size)
                            except:
                                pass

                            if temp_size == '':
                                try:
                                    temp_size = re.findall(u'面积 ?(\d+)', te)[0]
                                    room.size = int(temp_size)
                                except:
                                    pass

                            if temp_size == '':
                                try:
                                    temp_size = re.findall(u'(\d+.?\d*?) ?平方米', te)[0]
                                    room.size = int(temp_size)
                                except:
                                    pass
                    except Exception, e:
                        pass

                    try:
                        room.price = float(room_info.get('totalPrice'))
                        if int(room.price) <= 0:
                            continue
                    except Exception, e:
                        continue

                    try:
                        free_cancel_flag = room_info.get("cancellationType", {}).get('type', 0)
                        if free_cancel_flag == 0:
                            room.is_cancel_free = "No" # 不可取消
                        elif free_cancel_flag == 1:
                            room.is_cancel_free = "NULL" # 限时免费取消
                        elif free_cancel_flag == 2:
                            room.is_cancel_free = "NULL" # 收费取消
                    except Exception, e:
                        continue

                    room.return_rule = room_info.get('cancellationShowDesc', "").replace("<br>", '')
                    room.change_rule = ''

                    room.source_hotelid = self.user_datas['hotel_id']
                    room.hotel_name = self.user_datas['hotel_name']
                    room.city = self.user_datas['cid']
                    room.check_in = self.user_datas['check_in']
                    room.check_out = self.user_datas['check_out']
                    room.source = 'elong'
                    room.currency = 'CNY'
                    room.real_source = 'elong'
                    other_info = dict()
                    other_info['extra'] = {}
                    other_info['extra']['breakfast'] = breakfast_info
                    other_info['extra']['payment'] = room.pay_method
                    other_info['extra']['return_rule'] = room.return_rule
                    other_info['extra']['occ_des'] = "每间最多可入住{}人，如需加床或者带小孩儿，可能会收取费用。".format(room.occupancy)
                    room.others_info = json.dumps(other_info)
                    # print type(room.occupancy)
                    room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                                  room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                                  room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                                  room.rest, room.price, room.tax, room.currency, room.pay_method, \
                                  room.is_extrabed, room.is_extrabed_free, room.has_breakfast, \
                                  room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, \
                                  room.return_rule, room.change_rule, room.room_desc, \
                                  room.others_info, room.guest_info)
                    room_list.append(room_tuple)

            return room_list


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common import spider, utils
    from mioji.common.utils import simple_get_socks_proxy
    spider.slave_get_proxy = utils.simple_get_socks_proxy
    task = Task(source='elong')
    task.content = 'NULL&&448311&& 圣西罗住宿加早餐旅馆&&NULL&&1&&20171222'
    # task_list = [
    #     'PAR&&317421&&雷莱蒙马特酒店&&NULL&&4&&20171222',
    #     'WAW&&370326&&假日公园酒店&&3765&&1&&20170803',
    #     'ROM&&39269&&坦皮奥迪阿波罗酒店&&3023&&1&&20170803',
    #     'VIE&&371462&&维也纳城市公寓酒店 - 维也纳设计公寓 2&&3704&&1&&20170803',
    #     'AMS&&285004&&Jordaan Apartments Amsterdam Canal View&&378&&1&&20170803',
    #     'FRA&&331902&&法兰克福市弗莱明氏豪华酒店&&1246&&1&&20170803',
    #     'BER&&310362&&选帝侯大街柏灵公园酒店&&536&&1&&20171026',
    #     'PDX&&291571&&喀斯喀特车站波特兰机场旅馆&&2759&&1&&20171026',
    #     'AMS&&287863&&会议中心公寓酒店&&378&&1&&20170811',
    #     'ROM&&294945&&圣彼得无限酒店&&3023&&1&&20171028'
    # ]
    # task.content = task_list[0]
    task.ticket_info = {'occ': 2, 'cid': 12345}
    spider = ElongHotel(task)
    # spider.task = task
    result = spider.crawl(cache_config={'lifetime_sec': 10, 'enable': False})
    print result
    print spider.result
