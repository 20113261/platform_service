#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import re
from mioji.common.logger import logger
from random import randint
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common import parser_except
from mioji.common.class_common import Train
from datetime import datetime,timedelta
from lxml import html
import execjs
import traceback
import execjs
class CtripRailSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'ctripRail'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertHotel_room4
        'trains': {'version': 'InsertNewTrain'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'ctripRail': {'required': ['trains']}
    }

    def __init__(self, task=None):
        super(CtripRailSpider, self).__init__(task)

        if task:
            self.process_variable()
        self.dept_id = None
        self.dept_id_en = None
        self.dest_id = None
        self.dest_id_en = None
        self.dept_time = None
        self.adult_count = '1'
        self.children_count = 0
        self.seniors = 0
        self.youth = 0
        self.passenger_count = '1'
        self.dept_city = None
        self.dest_city = None
        self.start_city_cn = None
        self.arrive_city_cn = None

        self.city_info_url = 'http://webresource.ctrip.com/ResTrainOnline/R9/Outie/JS/outiecity.js?2017_2_21_16_40_32.js'
        self.referer_url = ''

        self.query_url = 'http://rails.ctrip.com/international/Ajax/CommonHandler.ashx'
        # self.query_url = 'http://rails.ctrip.com/international/Ajax/AjaxHandler.ashx'
        #self.query_url = 'http://rails.ctrip.com/international/Ajax/QueryOutiePTPProd.ashx'
        self.query_url = 'http://rails.ctrip.com/international/Ajax/{0}.ashx'
        self.headers = {'Accept': '*/*',
                        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.6,ja;q=0.4,af;q=0.2,en;q=0.2,de;q=0.2',
                        'Cache-Control': 'max-age=0',
                        'Connection': 'keep-alive',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Host': 'rails.ctrip.com',
                        'Origin': 'http://rails.ctrip.com',
                        }
        self.id = None
        self.last_start_date = '00:00'
        self.dept_moment = None
        self.dept_time_floor = '06:00'
        self.dept_time_cap = '23:59'
        self.end = False

        self.count = 0 #计数
    def targets_request(self):
        if not self.dept_time:
            self.process_variable()

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def list_req():
            ret = {
                'req':
                    {
                        'url': self.referer_url,
                        'method': 'get'
                    },
                'user_handler': [self.get_post_id]
            }
            return ret
        yield list_req

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=[self.parse_trains])
        def pages_request():

            post_data = self.get_post_data()
            temp_data = json.loads(post_data['QueryParam'])
            temp_data['Handler'] = ''.join([self.interface,'1'])
            temp_data['Handler2'] = ''.join([self.interface,'2'])
            post_data['QueryParam'] = json.dumps(temp_data)
            ret = {
                'req':
                    {
                        'url': self.query_url.format(self.interface),
                        'method': 'post',
                        'headers': self.headers,
                        'data': post_data
                    },
                'data':
                    {
                        'content_type': 'string'
                    },
                'user_handler': [self.assert_resp]
            }
            return ret

        while not self.end and self.count <= 10:
            yield pages_request
            time.sleep(randint(0, 5))

    def process_variable(self):
        try:
            contentlist = self.task.content.split('&')
            self.dept_city = contentlist[0]
            self.start_city_cn = contentlist[1].encode('utf8')
            self.dept_city_id = contentlist[2].encode('utf8')
            mmp_day = contentlist[-1]
            self.startdata ='-'.join([mmp_day[:4],mmp_day[4:6],mmp_day[-2:]])
            self.backdata = str(datetime(int(mmp_day[:4]),int(mmp_day[4:6]),int(mmp_day[-2:])) + timedelta(3))[:10]
            self.dest_city = contentlist[3]
            self.arrive_city_cn = contentlist[4].encode('utf8')
            self.dest_city_id = contentlist[5].encode('utf8')
            dept_time = contentlist[6]
            self.dept_time = dept_time[
                             0:4] + '-' + str(int(dept_time[4:6])) + '-' + str(int(dept_time[6:8]))
        except Exception:
            raise parser_except.ParserException(parser_except.TASK_ERROR, 'ctripOtaRail::ctripOtaRail 任务格式错误')

        self.passenger_count = self.task.ticket_info.get('v_count', '1')
        self.adult_count = self.passenger_count
        self.children_count = 0
        self.seniors = 0
        self.youth = 0
        self.process_time()
        self.process_referer_url()

    def process_time(self):
        self.dept_moment = self.task.ticket_info.get('dept_time', None)
        # 验证
        if self.dept_moment:
            moment = self.dept_moment.split('_')[1]
            hour = int(moment.split(':')[0])
            self.dept_time_cap = hour_to_str(hour+1)
            self.dept_time_floor = hour_to_str(hour-1)

    def process_referer_url(self):
        self.referer_url = 'http://rails.ctrip.com/international/OutiePTPList.aspx?departureDate=%s&starttime=' \
                           '&adult=%s&child=%s&youth=%s&seniors=%s&searchType=0&pageStatus=0&passHolders=0' \
                           '&from=%s&to=%s&arriveDate=' % (
                               self.dept_time, self.adult_count, self.children_count,
                               self.seniors, self.youth, self.dept_city, self.dest_city)

    def get_post_id(self, req, resp):
        try:
            self.id = re.compile(r'id="PageLoadGUID".*/>').findall(resp)[0][25:-4]
            self.interface = ''
            content = html.fromstring(resp)
            js_str = content.xpath('//script[contains(text(),"dealer")]/text()')[0]
            interface_str = re.search(r'dealer (.+)(?=;)',js_str).group(1)
            self.interface = re.search(r'([a-zA-Z]+)',interface_str).group(1)
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, '网页获取id失败')
        self.headers['Referer'] = self.referer_url

    def get_post_data(self):
        PassengerType = {'AdultCount': str(self.adult_count),
                         'YouthCount': str(self.youth),
                         'ChildCount': str(self.children_count),
                         'OldCount': str(self.seniors)
                         }
        data = {"StartTime": self.dept_time_floor,
                "BackTime": self.dept_time,
                "StartDate": self.startdata,
                "BackDate": self.backdata,
                "StartCityCode": self.dept_city,
                "ArriveCityCode": self.dest_city,
                "PassengerType": PassengerType,
                "PassHolders": '0',
                "LastStartDate": self.last_start_date,
                "StartCityName": self.start_city_cn,
                "ArrivalCityName": self.arrive_city_cn,
                "TrvalType": 1,
                "Handler": "CommonHandler1",
                "Handler2": "CommonHandler2",
                "PageLoadGUID": self.id
                }

        postdata = {'QueryParam': json.dumps(data, ensure_ascii=False).replace(' ', '')}
        return postdata

    def assert_resp(self, req, res):

        phantomjs = execjs.get('PhantomJS')
        res = phantomjs.eval(res)
        resp = res
        if resp['Message']:
            self.end = True
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, "网站展示出人工验证")
        rst_status = resp['RstStatus']
        logger.info('ctrip rail RstStatus： %s', rst_status)
        print "rst_status:",rst_status,type(rst_status)
        if rst_status != 1:
            if rst_status == 4:
                self.end = True
                return
            if rst_status == 32:  # 突然全部返回32了，然后抛出异常还不退出
                pass
                #raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, "session中代理被换")
            if rst_status == 64:
                self.end = True
                raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, "一个未知新错误，肯定是被封了")
            if rst_status != 32:
                raise parser_except.ParserException(parser_except.EMPTY_TICKET, '请求数据无票')
        print "函数名：",self.assert_resp.__str__(),"end值：",self.end
    def parse_trains(self, req, res):

        trains = []
        phantomjs = execjs.get('PhantomJS')
        res = phantomjs.eval(res)
        print "是否结束：", self.end, self.last_start_date, res['LastStartDate']
        if self.end:
            return trains
        if res['RstStatus'] == 32:
            self.count += 1
            return trains
        self.judge_end(res['LastStartDate'])
        self.count = 0
        print "通过时间来判断是否结束：",self.end
        prodectList = res['ProductList']

        for product in prodectList:
            train_info = Train()
            cabin = []
            train_no = []
            train_corp = []
            duration_time = product['DurationTime']
            dur = re.compile(r'[0-9]{1,2}').findall(duration_time)
            Trains = product['Trains']
            for train in Trains:
                train_no.append(train['TrainName'])
                train_corp.append('NULL')
            cabin.append(product['FirstClass']
                         if 'FirstClass' in product else {})
            cabin.append(product['SecondClass']
                         if 'SecondClass' in product else {})
            for cla in cabin:
                if cla:
                    TrainPrice = cla['TrainPrice']
                    for Trainprice in TrainPrice:
                        change_rule = []
                        return_rule = []
                        sigments = Trainprice['Sigments']
                        for Sigment in sigments:
                            change_rule_content = Sigment['ChangeRules'] if Sigment['ChangeRules'] else 'NULL'
                            change_rule.append(change_rule_content)
                            return_rule_detail = Sigment['ChangeRulesDetail'] if Sigment['ChangeRulesDetail'] else 'NULL'
                            return_rule.append(return_rule_detail)
                        seat_type = []

                        if isinstance(Trainprice['ProductInfoForOrder'],(str,unicode)):
                            product_in_for_order = json.loads(
                                Trainprice['ProductInfoForOrder'])

                        product_list = product_in_for_order['productList']
                        for detail in product_list:
                            train_info.price = detail['Price']
                            seat_type.append(detail['PackageTypeName'])
                            # train_info.dept_station = product['FromCity'] + '站'
                            # train_info.dest_station = product['ToCity'] + '站'

                            ptp_segment_list = detail['ptpSegmentList']
                            train_type = []
                            stop_time = []
                            stop_id = []
                            for segment in ptp_segment_list:
                                train_type.append(segment['TrainModel'])
                                # 这里会由于Station中不包含segment['StartCityCode']或segment['CityArriveCode']导致出现异常返回错误码27
                                start_station = segment['StartCityCode']
                                arrive_station = segment['CityArrivedCode']
                                stop_id.append(start_station + '_' + arrive_station)
                                # stop_id.append(segment['StartCityCode']+'_'+segment['CityArrivedCode'])
                                # dept_time = segment['DepartureDateTime'].split(' ')
                                dept_time = segment['DepartureDateTime']
                                # dest_time = segment['ArrivalDateTime'].split(' ')
                                dest_time = segment['ArrivalDateTime']
                                # stop_time.append('T'.join(dept_time) + ':00_' + 'T'.join(dest_time) + ':00')
                                stop_time.append(
                                    dept_time + ':00_' + dest_time + ':00')
                                if train_info.dept_day == 'NULL':
                                    train_info.dept_day = segment[
                                                              'DepartureDateTime'][:10]
                            train_info.stop = len(stop_id) - 1
                            train_info.dept_city = self.dept_city_id
                            train_info.dest_city = self.dest_city_id
                            train_info.train_no = '_'.join(train_no)
                            train_info.train_corp = '_'.join(train_corp)
                            train_info.train_type = '_'.join(train_type)
                            train_info.stopid = '|'.join(stop_id)
                            train_info.stoptime = '|'.join(stop_time)
                            train_info.seat_type = '_'.join(
                                seat_type * len(stop_id))
                            train_info.real_class = train_info.seat_type
                            train_info.change_rule = '_'.join(change_rule)
                            train_info.return_rule = '_'.join(return_rule)
                            train_info.dept_station = stop_id[0].split('_')[0]
                            train_info.dest_station = stop_id[-1].split('_')[-1]
                            train_info.dept_time = stop_time[0].split('_')[0]
                            train_info.dest_time = stop_time[-1].split('_')[-1]
                            train_info.dur = int(dur[0]) * 3600 + int(dur[1]) * 60
                            train_info.tax = 0
                            train_info.daydiff = '_'.join(['0'] * len(stop_id))
                            train_info.currency = 'CNY'
                            train_info.source = 'ctrip'
                            train_info.dept_id = stop_id[0].split('_')[0]
                            train_info.dest_id = stop_id[-1].split('_')[1]
                            if train_info.dept_day >= str(datetime.now())[:10]:
                                trains.append(train_info.to_tuple())
                            else:
                                raise parser_except.ParserException(parser_except.EMPTY_TICKET,'出现假数据')

        return trains

    def judge_end(self, last_date):
        if compare_time(last_date, self.last_start_date):
            self.end = True

        if compare_time(self.dept_time_cap, last_date):
            self.end = True
        self.last_start_date = last_date


def hour_to_str(time_num):
    if time_num < 0 or time_num > 24:
        return
    if time_num < 10:
        return '0%s:00' % time_num
    else:
        return '%s:00' % time_num


def compare_time(time1, time2):
    hour1, minute1 = time1.split(':')
    hour2, minute2 = time2.split(':')

    if int(hour1) > int(hour2):
        return False
    if int(hour1) == int(hour2):
        if int(minute1) > int(minute2):
            return False
    return True


def get_id(xxxx):
    from random import sample
    ip = ['10.19.159.84:34096', '10.10.233.246:34281', '110.10.224.195:34421', '10.19.170.112:34528']
    return sample(ip, 1)[0]


if __name__ == '__main__':

    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy,simple_get_http_proxy
    from mioji.common import spider
    import httplib

    #httplib.HTTPConnection.debuglevel = 1
    #spider.get_proxy = simple_get_http_proxy
    spider.get_proxy = simple_get_socks_proxy
    task = Task()

    task.content = "ITMIL&米兰&111111&FRLYS&里昂&222222&20171111"
    task.content = "ITRMA&罗马&111111&FRNCE&尼斯&222222&20171111"
    #task.content = "FRPAR&巴黎&111111&ITMIL&米兰&222222&20171111"
    #task.content = "ITVCE&威尼斯&111111&ESMAD&马德里&222222&20171111"
    task.content = "ITMIL&米兰&111111&FRLYS&里昂&222222&20171111"
    #task.content = "BEBRU&布鲁塞尔&111111&DEFRA&法兰克福&222222&20171111"
    #task.content = "ITFLR&佛罗伦萨&111111&CHZRH&苏黎世&222222&20171111"
    #task.content = 'ITABQ&圣文森特&12261&ITQBS&布雷西亚&10355&20171030'
    #task.content = 'FRHEI&特内&12771&FRGNB&格勒诺布尔&10204&20171028'
    #task.content = 'DEBEF&曼海姆&10135&DEGFW&格赖夫斯瓦尔德&12085&20171101'
    # task.ticket_info['dept_time'] = '20170507_10:59'
    contents = [
        'ITMIL&米兰&111111&FRLYS&里昂&222222&20171111',
        'ITRMA&罗马&111111&FRNCE&尼斯&222222&20171111',
        'ITVCE&威尼斯&111111&ESMAD&马德里&222222&20171111',
        'FRPAR&巴黎&111111&ITMIL&米兰&222222&20171111',
        'BEBRU&布鲁塞尔&111111&DEFRA&法兰克福&222222&20171111',
        'ITFLR&佛罗伦萨&111111&CHZRH&苏黎世&222222&20171111',
        'ITABQ&圣文森特&12261&ITQBS&布雷西亚&10355&20171030',
        'FRHEI&特内&12771&FRGNB&格勒诺布尔&10204&20171028',
        'DEBEF&曼海姆&10135&DEGFW&格赖夫斯瓦尔德&12085&20171101',
        'FRADI&敦刻尔克&10389&FRNTE&南特&10199&20171108',
        'FRADI&敦刻尔克&10389&FRLIL&里尔&10149&20171108',
        'FRADI&敦刻尔克&10389&FRCFV&古桑维尔&12624&20171108',
        'FRADI&敦刻尔克&10389&FREVJ&蒙特里夏尔&12837&20171108',
        'FRDPE&迪耶普&12851&FRAIE&普罗旺斯&11103&20171108',
        'FRDPE&迪耶普&12851&FRIJL&博凯尔&12607&20171108',
    ]
    for content in contents:
        task.content = content
        start = datetime.now()
        rail = CtripRailSpider()
        task.ticket_info = {'dept_time':'20171024_13:00'}
        rail.task = task
        print rail.crawl()
        print '共有', len(rail.result['trains']), '张票'
        print json.dumps(rail.result['trains'], ensure_ascii=False)
        end = datetime.now()
        import csv
        with open('result.csv','a+') as result:
            writer = csv.writer(result)
            writer.writerow((task.content,end-start,len(rail.result['trains']),start,end))

