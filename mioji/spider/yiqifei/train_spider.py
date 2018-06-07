#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
@Time : 17/5/4 上午10:02
@Author : Li Ruibo
'''

import json
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

from mioji.common.spider import Spider,request,PROXY_REQ
from mioji.common.class_common import Train
import mioji.common.parser_except as parser_except
from lxml import html as HTML, etree
import copy
import datetime


DAY_FORMAT = '%Y-%m-%d' #定义日期格式
TIME_FORMAT = '%Y-%m-%d %H:%M'


class yiqiFeiSpider(Spider):

    source_type = 'yiqifeiRail'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertHotel_room4
        'train': {'version': 'InsertNewTrain'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'yiqifeiRail': {'required': ['train']}
    }

    def __init__(self,task=None):
        super(yiqiFeiSpider,self).__init__(task)

    def targets_request(self):

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def get_cookies():
            main_page_url = 'http://tour.yiqifei.com/Europe/'
            return {'req': {'url': main_page_url, 'headers': '', 'method': 'get'},
                    'data': {'content_type': 'string'},
                    'user_handler': [self.__get_session_cookies]
                    }

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def get_cache_key():
            post_data = {
                'IsRoundTrip': 'false',
                'CityCodeFrom': '',
                'CityNameFrom': '',
                'CityCodeTo': '',
                'CityNameTo': '',
                'DateDepart': '',
                'TimeDepartHigh': '',
                'TimeDepartLow': '',  # 出发时间段：从TimeDepartLow到TimeDepartHigh
                'DateBack': '2017-05-28',
                'TimeBackHigh': '12:00',
                'TimeBackLow': '08:00',
                'Adults': '0',
                'Children': '0',
                'Youths': '0',
                'Seniors': '0',
            }
            if self.task.ticket_info:
                ticket_info = self.task.ticket_info
                post_data['Adults'] = ticket_info.get('v_count', 1)  # 人数该如何分配
                dept_time = ticket_info.get('dept_time', None)  # %Y%m%d_%H:%M
                # 判断dept_time落在哪个时间段，得到TimeDepartHigh，TimeDepartLow
                time_low, time_high = self.__get_high_low_time(dept_time, '%Y%m%d_%H:%M')
                time_spans = [(time_low, time_high)]
            else:
                time_spans = [('00:00', '04:00'), ('04:00', '08:00'), ('08:00', '12:00'), ('12:00', '16:00'),
                                  ('16:00', '20:00'), ('20:00', '24:00')]
                post_data['Adults'] = 1


            contents = self.task.content.split('&')
            #print contents
            post_data['CityCodeFrom'] = contents[0]
            post_data['CityNameFrom'] = contents[1]
            post_data['CityCodeTo'] = contents[2]
            post_data['CityNameTo'] = contents[3]
            # 20170923 -- 2017-09-23 日期格式需转化为yiqifei的特定格式
            raw_date_str = contents[4]
            post_data['DateDepart'] = raw_date_str[0:4] + '-' + raw_date_str[4:6] + '-' + raw_date_str[-2:]

            headers = {
                'Cache-Control': 'no-cache',
                'Host': 'tour.yiqifei.com',
                'Connection': 'keep-alive',
                'Content-Length':None,
                'Origin': 'http://tour.yiqifei.com',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': '*/*',
                'Cookie': '.ASPXANONYMOUS=%s;ASP.NET_SessionId=%s'%(self.user_datas['ASPXANONYMOUS'],self.user_datas['NET_SessionId']),
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'http://tour.yiqifei.com/Europe/',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
            }
            cache_key_page_url = 'http://tour.yiqifei.com/Europe/SearchPTP'
            posts_data = []
            for index, each in enumerate(time_spans):
                _post_data = copy.copy(post_data)
                _post_data['TimeDepartLow'] = each[0]
                _post_data['TimeDepartHigh'] = each[1]
                posts_data.append(_post_data)

            return [{'req': {'url': cache_key_page_url, 'headers': headers, 'method': 'post', 'data': posts_data[i]},
                     'data': {'content_type': 'string'},
                     'user_handler': [self.__get_cachekeys]  # 获取当前定义的查询数据的cachekey
                     } for i in range(len(time_spans))]


        @request(retry_count=5, proxy_type=PROXY_REQ, binding=['train'])
        def get_link_page():
            '''
            每个请求是有binding的
            在spider.py中parse成员方法中的第949行，根据binding获取解析方法，如 'train'获取的是parse_train方法
            然后，使用该方法进行解析
            :return: 
            '''
            cache_keys = self.user_datas['all_cache_keys']
            funcs = []
            for each in cache_keys:
                funcs.append(self.__get_link_page_by_cachekey(each))
            return funcs

        yield get_cookies
        if self.user_datas['ASPXANONYMOUS'] and self.user_datas['NET_SessionId']:
            yield get_cache_key
            yield get_link_page




    def parse_train(self,req,data):
        all_train = []
        content = req['resp'].text
        try:
            json_train = json.loads(content)
        except ValueError as ve:
            #print '[JSON 返回格式不对]==============返回内容是：{cont}'.format(cont=content)
            raise parser_except.ParserException(parser_except.ParserException.PROXY_INVALID,'未获取完整的火车JSON数据.')
        else:
            train_detail_forward = json_train['ForwardItinerary']['TrainSolutions']
            train_detail_return = json_train['ReturnItinerary']['TrainSolutions']
            train_detail_forward.extend(train_detail_return)
            for each_train in train_detail_forward:
                trains_info = each_train['TrainSegments']#有可能需要转车
                train_no = []  # 列车号
                stop_time_all = []
                day_diff_all = []
                trans_num_index_max = len(trains_info)-1#总共需要换乘车的数量
                for index,train_info in enumerate(trains_info):
                    _dep_day = train_info['DepDate']
                    _dep_time = train_info['DepTime']
                    _dest_day = train_info['ArrDate']
                    _dest_time = train_info['ArrTime']

                    date_dep = datetime.datetime.strptime(_dep_day,DAY_FORMAT)
                    date_dest = datetime.datetime.strptime(_dest_day,DAY_FORMAT)
                    date_diff = (date_dest-date_dep).days
                    if date_diff > 0:
                        day_diff_all.append('1')
                    else:
                        day_diff_all.append('0')

                    dept_city = train_info['DepCityName']
                    dept_station = train_info['DepStationName']
                    dept_day = _dep_day
                    dept_time =  dept_day + ' ' + _dep_time
                    dest_city = train_info['ArrCityName']
                    dest_station = train_info['ArrStationName']
                    dest_day = _dest_day
                    dest_time =   dest_day +' '+ _dest_time

                    stop_time_per_train = '{0}_{1}'.format(dept_time,dest_time)
                    stop_time_all.append(stop_time_per_train) #所有火车的出发、到站时间
                    train_no.append(train_info['EquipmentCode']+train_info['TrainNumber']) #所有火车的列车号

                    if index == 0:
                        dept_time_all_trip =  dept_time #整个行程的起始时间，区别于每个列车的起始时间dept_time
                        dept_day_all_trip = dept_day
                        dept_city_all_trip = dept_city
                        dept_station_all_trip = dest_station
                    if index == trans_num_index_max:
                        dest_city_all_trip = dest_city
                        dest_station_all_trip = dest_station
                        dest_time_all_trip = dest_time


                dur = (datetime.datetime.strptime(dest_time_all_trip,TIME_FORMAT)-datetime.datetime.strptime(dept_time_all_trip,TIME_FORMAT)).seconds
                train_no = '_'.join(train_no)
                stop_time_all = '|'.join(stop_time_all)
                day_diff_all = '_'.join(day_diff_all)
                cabins_info = each_train['TrainCabinPrices'] #获取不同座位类型信息，比如，A等，B等
                for each_cabin in cabins_info:
                    train = Train()
                    train.train_no = train_no  # 班次
                    train.train_type = 'NULL'  # 火车类型
                    train.train_corp = 'NULL'  # 运营公司
                    train.dept_city = dept_city_all_trip  # 始发城市
                    train.dept_station = dept_station_all_trip # 始发站
                    train.dept_time = dept_time_all_trip  # 始发时间
                    train.dept_day = dept_day_all_trip
                    train.dest_city = dest_city_all_trip  # 目的地城市
                    train.dest_station = dest_station_all_trip  # 终点站
                    train.dest_time = dest_time_all_trip  # 到站时间
                    train.dept_id = self.task.content.split('&')[0]
                    train.dest_id = self.task.content.split('&')[2]
                    train.dur = dur # 耗时
                    train.price = each_cabin['Price']  # 价格
                    train.tax = -1.0  # 税费
                    train.currency = 'EUR'  # 货币类型?
                    train.seat_type = each_cabin['CabinClass'].replace('-','_')  # 座位类型
                    train.source = 'yiqifei'  # ？
                    train.return_rule = 'NULL'  # ？
                    train.stop = trans_num_index_max  #需要倒车的次数
                    train.stop_station = 'NULL'  # ？
                    train.stopid = 'NULL'
                    train.stoptime = stop_time_all
                    train.real_class = train.seat_type  # ？
                    train.daydiff = day_diff_all

                    train.change_rule = 'NULL'
                    train.train_facilities = 'NULL'
                    train.ticket_info = 'NULL'
                    train.electric_ticket = 'NULL'
                    train.promotion = 'NULL'
                    train.others_info = 'NULL'
                    train.change_rule = 'NULL'
                    train.facilities = 'NULL'
                    train.ticket_type = each_cabin['TicketType']
                    train.rest = -1
                    all_train.append(train.to_tuple())

            return all_train


    def __get_cachekeys(self,req, data):
        if 'all_cache_keys'  not in self.user_datas:
            self.user_datas['all_cache_keys'] = []
        try:
            self.user_datas['all_cache_keys'].append(json.loads(req['resp'].content)['cacheKey'])
        except ValueError as ve:
            # 若抛出异常，代表获取cache_失败，则抛出22异常，以供框架重新发起请求
            #print '[JSON 返回格式不对]==============返回内容是：{cont}'.format(cont=req['resp'].content)
            raise parser_except.ParserException(parser_except.ParserException.PROXY_INVALID,'未获取完整的cacheKey.')


    def __get_session_cookies(self, req, data):
        try:
            self.user_datas['ASPXANONYMOUS'] = req['resp'].cookies['.ASPXANONYMOUS']
            self.user_datas['NET_SessionId'] = req['resp'].cookies['ASP.NET_SessionId']
        except Exception:
            raise parser_except.ParserException(parser_except.ParserException.PROXY_INVALID, '未获取完整的cookie.')


    def __convert_date(self, date_str, date_format):
        import re
        #若遇到的结束high time为24:00则将其转换为第二天的00时。注：datetime模块不支持24
        if re.match('.*24:00(:\d\d)?',date_str):
            date_str_new = date_str.replace('24:00', '00:00')
            date_new = datetime.datetime.strptime(date_str_new,date_format) + datetime.timedelta(days=1)#处理跨天问题
        else:
            date_new = datetime.datetime.strptime(date_str,date_format)
        return date_new

    def __compare_date(self, date1_str,date2_str, date_format):
        """
        若date1 > date2 : 1
        -1,0,1 : date1 < = > date2
        :param date1: 
        :param date2: 
        :param date_format: 
        :return: 
        """
        date1 = self.__convert_date(date1_str,date_format)
        date2 = self.__convert_date(date2_str, date_format)
        delt_days = (date1 - date2).days
        delt_seconds = (date1-date2).seconds
        if delt_days == 0 and delt_seconds==0:
            return 0
        elif delt_days == 0 and delt_seconds>0:
            return 1
        elif delt_days < 0 and delt_seconds>0:
            return -1

    def __get_high_low_time(self,dept_time, date_format):
        time_span = [('%s_00:00', '%s_04:00'), ('%s_04:00', '%s_08:00'), ('%s_08:00', '%s_12:00'),
                     ('%s_12:00', '%s_16:00'),
                     ('%s_16:00', '%s_20:00'), ('%s_20:00', '%s_24:00')]
        dept_day = dept_time.split('_')[0]
        for each in time_span:
            start = each[0] % (dept_day)
            end = each[1]%(dept_day)
            res_low = self.__compare_date(dept_time, start,date_format)#datetime不支持24:00,需将天数加一换成00:00
            res_high = self.__compare_date(dept_time, end,date_format)
            if res_low > 0 and res_high < 0:
                time_depart_low = start.split('_')[1]
                time_depart_high = end.split('_')[1]
                return time_depart_low, time_depart_high



    def __get_link_page_by_cachekey(self,cachekey):
        headers = {
            'Host': 'tour.yiqifei.com',
            'Connection': 'keep-alive',
            'Origin': 'http://tour.yiqifei.com',
            'Content-Length': None,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://tour.yiqifei.com/Europe/PTPList?cacheKey=%s' % cachekey,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cookie': '.ASPXANONYMOUS=%s; _yqfck=n.e6214579.80a9423040e70195;\
                                              __utma=63496615.390717990.1493861750.1493864258.1493864258.1;\
                                               __utmz=63496615.1493864258.1.1.utmcsr=tour.yiqifei.com|utmccn=(referral)|utmcmd=referral|utmcct=/Europe; \
                                               ASP.NET_SessionId=%s; _ga=GA1.2.390717990.1493861750; _gid=GA1.2.2117997704.1494471170'%(self.user_datas['ASPXANONYMOUS'],self.user_datas['NET_SessionId'])
        }

        list_page_url = 'http://tour.yiqifei.com/Europe/GetSearchPTP'
        form_data = {'cachekey': cachekey}
        return {'req': {'url': list_page_url, 'headers': headers, 'method': 'post', 'data': form_data},
                'data': {'content_type': 'string'}}


if __name__ == '__main__':
    '''
    有用的测试信息：
        1. 既有中转票，又有直达票：'FRPAR','PARIS','DEFRA','FRANKFURT','20170528'
    '''
    from mioji.common.task_info import Task
    from mioji.common import  spider
    from mioji.common.utils import simple_get_http_proxy
    #spider.get_proxy = simple_get_http_proxy
    task = Task()
    task.content = '%s&%s&%s&%s&%s'%('FRPAR','PARIS','DEFRA','FRANKFURT','20170527')#任务内容：出发地代码 出发城市 终点站代码 终点站城市 出发日期
    #task.content = 'ITBLQ&BOLOGNA&DENUE&NUREMBERG&20170527' # code: 0, 不存在该城市名称
    #task.content = 'GBCWL&CARDIFF&GBCTR&CHESTER&20170527' # code:29, 没有数据
    #task.content = 'SEAAA&MALMO&FRDIJ&DIJON&20170529'
    #task.content = 'DEXXO&波茨坦&FRRHE&兰斯&20170525' #29
    task.ticket_info['v_seat_type'] = ''
    task.ticket_info['v_count'] = '1'
    task.ticket_info['dept_time'] = '20170528_10:30'
    task.ticket_info['dest_time'] = ''
    task.ticket_info['v_age'] = ''
    task.ticket_info['v_hold_seat'] = ''
    #task.ticket_info = {}#先查找所有时间段的信息

    spider = yiqiFeiSpider()
    spider.task = task
    spider.req_count = 5
    #res = spider.crawl(cache_config={'enable': False})
    res = spider.crawl()
    print('[Debug res]:%d'%res)
    print(spider.result)