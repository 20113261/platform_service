#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import re
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.mioji_struct import MFlight,MFlightLeg,MFlightSegment,FOR_FLIGHT_DATE
from hnair_flight_lib import get_postdata, get_promotion, get_city_no
#from common_lib import process_ages, seat_type_to_queryparam
#from base_data import port_city
#from mioji.common.logger import logger

class HnairFlightSpider(Spider):
    """
    海航单程爬虫
    """
    source_type = 'hnairFlight'

    targets = {
        'Flight':{'version': 'InsertNewFlight'}
    }

    old_spider_tag = {
        'hnairFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        self.header = {
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
            "Referer":"www.baidu.com"
        }
        self.postdata = ""
        self.task_info = None
        # 可爱的海航，需要请求5个接口来得到最终的数据
        self.first_get_url = ""
        self.second_post_url = ""
        self.third_get_url = 'http://new.hnair.com/hainanair/ibe/common/processSearchEntry.do?fromEntryPoint=true'
        self.fourth_post_url = 'http://new.hnair.com/hainanair/ibe/common/processSearch.do'
        self.final_get_url = 'http://new.hnair.com/hainanair/ibe/air/searchResults.do'

        # if self.task is not None:
        #     self.process_task_info()

    def targets_request(self):

        #处理生成task_info信息
        if self.task_info is None:
            self.process_task_info()

        @request(retry_count=3,proxy_type=PROXY_REQ,user_retry_count=0)
        def first_get_request():
            # 单程

            '''
            DD1:出发日期
            DD2:回程日期(单程的话不用填写)
            TA:成人人数
            TC:儿童人数
            ORI:出发地三字码
            DES:目的地三字码
            SC:舱位等级(Y:经济舱，F:商务舱)
            FLC:(1:单程，2:往返)
            '''
            self.first_get_url = "http://new.hnair.com/hainanair/ibe/deeplink/ancillary.do?DD1={dept_day}&DD2=&TA={adult_sum}&TC={child_sum}&TI=&TM=&TP=&ORI={dept_id}&DES={dest_id}&SC={seat_type}&ICS=F&PT=F&FLC=1&NOR=&PACK=T&HC1=&HC2=&NA1=&NA2=&NA3=&NA4=&NA5=&NC1=&NC2=&NC3=&NC4=".format(**self.task_info.__dict__)

            self.second_post_url = self.first_get_url
            print(self.first_get_url)
            return {
                'req':{'url':self.first_get_url,'method':'get','headers':self.header},
            }

        @request(retry_count=3,proxy_type=PROXY_FLLOW,user_retry_count=0)
        def second_post_request():
            data = {
                'ConversationID':'',
                'ENCRYPTED_QUERY':'',
                'QUERY':'',
                'redirected':'true'
            }
            self.header = {
                "Referer":self.first_get_url,
            }
            return {
                'req':{'url':self.second_post_url,'method':'post','headers':self.header,'data':data,'verify':False},
            }

        @request(retry_count=3,proxy_type=PROXY_FLLOW,user_retry_count=0)
        def third_get_request():
            self.header = {
                "Referer":self.second_post_url,
            }
            return {
                'req':{'url':self.third_get_url,'method':'get','headers':self.header,'verify':False},
            }

        @request(retry_count=3,proxy_type=PROXY_FLLOW,user_retry_count=0)
        def fourth_post_request():
            self.header = {
                "Referer":self.third_get_url,
            }
            return {
                'req':{'url':self.fourth_post_url,'method':'post','headers':self.header,'verify':False},
            }

        @request(retry_count=3,proxy_type=PROXY_FLLOW,user_retry_count=0,binding=self.parse_Flight)
        def final_get_request():
            self.header = {
                "Rederer":self.fourth_post_url,
            }
            return {
                'req':{'url':self.final_get_url,'method':'get','headers':self.header,'verify':False},
            }

        return [first_get_request,second_post_request,third_get_request,fourth_post_request,final_get_request]

    def parse_Flight(self,req,data):
        data = data.encode('utf-8')
        for_flight_date = FOR_FLIGHT_DATE[:-3]
        result = []
        # 这个正则用来匹配出搜索结果页面的源信息中每组行程的信息list，list中每个元素是一班飞机
        legs_RE = r"var Flight = \{\};\s*var tags = \{\};\s*var sequenceNumber = '\d*';\s*var position = '\d*';\s*var FlightInfos = \{\};\s*FlightInfos\.outBoundFlightInfo = \{\};\s*var outBoundFlightInfo = \{\};\s*outBoundFlightInfo\.legs = \{\};([\s\S]*?)Flight.FlightInfos = FlightInfos;\s*Flight\.Prices = Prices;\s*Flight\.TpaInfos = TpaInfos;\s*Flight\.Brands = Brands;\s*Flight\.Sequence = sequenceNumber;\s*Flight\.firstDepartureTime ="
        # 拿到每张leg组成的list
        legs_list = re.findall(legs_RE,data)
        for leg_temp in legs_list:
            # 这个正则用来匹配出每组行程中的每种价格
            # ['2060.0', '6470.0']
            price_list_RE = r"var fareinfo = \{\};\s*var flightSegmentRPH = '.*';\s*fareinfo\.CabinType = '.*';\s*fareinfo\.isVcabin='.*';\s*fareinfo\.EarnMile = '.*';\s*fareinfo\.BrandName = '.*';\s*fareinfo\.BaseAmount = '.*';\s*fareinfo\.TotalAmount = '.*';\s*fareinfo\.CNTax = '.*';\s*fareinfo\.YQTax = '.*';\s*fareinfo\.YRTax = '.*';\s*fareinfo\.TotalFare = '(.*)';\s*fareinfo.fareFamilyName = '.*';\s*Price.fareinfo\[flightSegmentRPH\] = fareinfo;"
            price_list = re.findall(price_list_RE,leg_temp)
            print price_list
            for price_temp in price_list:
                # 根据每个价格，创建一个MFlight
                if '0.0' == price_temp or '' == price_temp:
                    continue
                mflight = MFlight(MFlight.OD_ONE_WAY)
                mflight.price = float(price_temp)
                mflight.tax = float(0)
                mflight.currency = 'CNY'
                mflight.source = 'hnair::hnair'
                leg = MFlightLeg()
                # [(u'HU', u'7971', u'2018-01-31', u'01:00', u'XIY', u'2018-01-31', u'05:55', u'FCO', u'332'), (u'AZ', u'324', u'2018-01-31', u'14:50', u'FCO', u'2018-01-31', u'17:00', u'CDG', u'321')]
                flightInfo_RE = r"flightInfo\.AirlineCarrierCN = '.*';\s*flightInfo\.AirlineCarrierEN = '.*';\s*flightInfo\.AirlineMarketingEN = '(.*)';\s*flightInfo\.AirlineMarketingCN = '.*';\s*flightInfo\.FlightNumber = '(.*)';\s*flightInfo\.OperatingFlightNumber = '.*';\s*flightInfo\.StopQuantity = '.*';\s*flightInfo\.seatNum = '.*';\s*flightInfo\.DepartureDate = '(.*)';\s*flightInfo\.DepartureTime = '(.*)';\s*flightInfo\.DepartureAirport = '.*';\s*flightInfo\.DepartureIATA = '(.*)';\s*flightInfo\.DepartureTerminal = '.*';\s*flightInfo\.ArrivalDate = '(.*)';\s*flightInfo\.ArrivalTime = '(.*)';\s*flightInfo\.ArrivalAirport = '.*';\s*flightInfo\.ArrivalIATA = '(.*)';\s*flightInfo\.ArrivalTerminal = '.*';[\s\S]*?flightInfo.EquipType = '(.*)';"
                flightInfo = re.findall(flightInfo_RE,leg_temp)
                print flightInfo
                for seg_temp in flightInfo:
                    print seg_temp
                    seg = MFlightSegment()
                    seg.flight_no = seg_temp[0] + seg_temp[1]
                    seg.dept_id = seg_temp[4]
                    seg.dest_id = seg_temp[7]
                    seg.seat_type = 'ECONOMY' if 'Y' == self.task_info.__dict__.get('seat_type','Y') else 'BUSINESS'
                    seg.set_dept_date(seg_temp[2]+'T'+seg_temp[3], for_flight_date)
                    seg.set_dest_date(seg_temp[5]+'T'+seg_temp[6], for_flight_date)
                    seg.plane_type = seg_temp[-1]
                    leg.append_seg(seg)
                mflight.append_leg(leg)
                temp_tuple = mflight.convert_to_mioji_flight().to_tuple()
                result.append(temp_tuple)

        return result


    def response_callback(self,request_template, resp):
        # 这里是传说中的回调函数
        print "-------response_callback--------" + "True" if request_template['resp'] == resp else "False"

    def process_post_data(self,req,data):
        pass


    def process_task_info(self):
        task = self.task

        ticket_info = task.ticket_info
        print 'here------',ticket_info
        task_info = type('task_info', (), {})

        # 从ticket_info中获取舱位等级信息,默认为经济舱
        seat_type = ticket_info.get('v_seat_type', 'E')
        if 'E' == seat_type:
            seat_type = 'Y'
        elif 'B' == seat_type:
            seat_type = 'F'
        else:
            seat_type = 'Y'
        # 从ticket_info中获取成人人数，默认为1
        adult_sum = str(ticket_info.get('v_adult',1))
        # 从ticket_info中获取儿童人数，默认为0
        child_sum = str(ticket_info.get('v_child',0))
        #count = int(ticket_info.get('v_count', '1'))
        #ages = ticket_info.get('v_age', '-1')
        try:
            dept_id, dest_id, dept_day = task.content.split('&')
            #dept_id = port_city.get(dept_port, dept_port)
            #dest_id = port_city.get(dest_port, dest_port)
            #adults, childs, infants = process_ages(count, ages)
        except:
            raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                'Content Error:{0}'.format(self.task.content))

        task_info.dept_id = dept_id
        task_info.dest_id = dest_id
        task_info.dept_day = re.sub('(\d\d\d\d)(\d\d)(\d\d)', r'\1-\2-\3', dept_day)
        task_info.seat_type = seat_type
        task_info.adult_sum = adult_sum
        task_info.child_sum = child_sum
        # infants = 0
        # childs = 0
        # adults = count

        #task_info.infants, task_info.childs, task_info.adults = str(infants), str(childs), str(adults)
        #task_info.cabin = seat_type_to_queryparam(seat_type)

        try:
            pass
            # val = get_city_no(dept_id)
            #task_info.deptcity_name = urllib.quote(val['city_name'].decode('utf8').encode('gbk'))
            #task_info.dept_city_en_name = val['city_en_name'].lower().replace('.', '').replace(' ', '')
            #task_info.deptcity_no = val['city_id']
        except:
            raise parser_except.ParserException(51,
                                                'ctripFlight::无法找到suggestion')
        self.task_info = task_info



if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug

    mioji.common.spider.get_proxy = simple_get_socks_proxy
    # httpset_debug()

    task = Task()
    #单程
    #XIY：西安，WAS：华盛顿, PEK:北京 CDG:bali
    # task.content = 'PEK&XIY&20180131'
    # task.content = 'PEK&CDG&20180205'
    task.content = 'PEK&CDG&20180205'
    #task.content = 'PAR&XIY&20180131'
    # task.content = 'KIX&XIY&20180131'
    task.ticket_info = {
        'v_seat_type': 'B',
        'v_adult': 2,
        'v_child': 0,
    }
    spider = HnairFlightSpider()
    spider.task = task
    #print spider.crawl(cache_config={'enable':True})
    print spider.crawl()
    print spider.result
