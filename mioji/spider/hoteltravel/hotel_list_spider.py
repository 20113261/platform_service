#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

import re, json
from mioji.common.task_info import creat_hotelParams
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common import parser_except
from mioji.models.city_models import get_suggest_city
import hotellist_parse

DATE_F = '%Y年%m月%d日'
CAL_F = '%d/%m/%Y'
URL = 'http://www.hoteltravel.com/search/hotels.aspx'
URL_HOTEL = 'http://www.hoteltravel.com/search/includes/generatemandatorydata.aspx'

hd = {
        'Host': 'www.hoteltravel.com',
        'Origin': 'http://www.hoteltravel.com',
        'Accept': 'text/html, application/xhtml + xml, application/xml;q = 0.9, image/webp, */*;q = 0.8',
        'Referer': 'http://www.hoteltravel.com/',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh - CN, zh;q = 0.8, und;q = 0.6',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type':'application/x-www-form-urlencoded',
        # 'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.59 Safari/537.36',
    }

def crate_postdata(task_p, self_p):
    
    ps = self_p['code'].split('*')
    
    city, country = ps[0], ps[-1]
    if 'city_zh_name' in self_p.keys():
        search = self_p['city_zh_name']
    else:
        search = self_p['cityname']
    print search
    data = {
        'domain':'http://www.hoteltravel.com/', 'language':'cn', 'global':'',
        'city':city, 'country':country,
        'type':'search', 'searchkey':self_p['kv'], 'cookieterm':'', 'countryurl':'', 'cityurl':'', 'hotelcode':'',
        'cFreeSearch': search,
        'cFreeSearchHotel':'',
        'arrivaldate': task_p.format_check_in(DATE_F), 'calendararr':task_p.format_check_in(CAL_F),
        'depaturedate':task_p.format_check_out(DATE_F), 'calendardept':task_p.format_check_out(CAL_F),
        'ddlNoOfRooms':task_p.rooms_count
    }
    
    for index in xrange(0, task_p.rooms_count):
        r = task_p.rooms_required[index]
        pstr_index = str(index + 1) 
        if index == 0:
            data['ddlNoOfAdults'] = r.adult
        else:
            data['ddlNoOfAdults' + pstr_index] = r.adult
        
        data['ddlNoOfChild' + pstr_index] = r.child
        
        for c_index in xrange(0, r.child):
            age = r.child_age[c_index]
            age = age if age >= 2 else 0
            data['ddlChildAge1' + str(c_index + 1)] = age
        
    
    return data

class HotelListSpider(Spider):
    
    source_type = 'hoteltravelListHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel':{},
        'room':{'version':'InsertHotel_room4'}
        }
    
    # 设置上不上线 unable
    # unable = True

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'hoteltravelListHotel':{'required':['room']}
        }

    def targets_request(self):
        try:
            mjcity_id = self.task.content.split('&')[0]
            task_p = creat_hotelParams(self.task.content)
            self.user_datas['mjcity_id'] = mjcity_id
            self_p = get_suggest_city('hoteltravel', mjcity_id)
            if not self_p:
                raise parser_except.ParserException(parser_except.TASK_ERROR, 'can’t find suggest config city:[{0}]'.format(mjcity_id))
        except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR, 'parse task occur some error:[{0}]'.format(e))
        
        data = crate_postdata(task_p, self_p)

        self.user_datas['adult'] = task_p.adult
        self.user_datas['check_in'] = task_p.check_in
        self.user_datas['check_out'] = task_p.check_out
        self.user_datas['night'] = task_p.night
        
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def params_request():
            print data
            return {'req':{'method':'post', 'url':URL, 'data':data, 'headers':hd},
                    'user_handler':[self.parse_hotel_params]}
        @request(retry_count=3, proxy_type=PROXY_REQ)            
        def currency_to_RMB():
            url = "http://www.hoteltravel.com/utility/currencyexchange.aspx?"
            return {
                'req':{
                    'url':url,
                    'headers':hd
                },
                'data':{'content_type':'string'},
                'user_handler':[self.parser_currency_to_RMB]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['hotel', 'room'])
        def hotels_request():
            return {'req':{'url':URL_HOTEL, 'headers':hd, 'params':{'strSingleString':self.user_datas['SelectPass']}},
                'data':{'content_type':self.convert_hotel_json}, }
        
        return [params_request,currency_to_RMB, hotels_request]
    
    def parser_currency_to_RMB(self, req, data):
        page = data.split('"')[1][:-1]
        page = eval(page)
        self.user_datas['currency_rates'] = page

    def respon_callback(self, req, resp):
        print 'r url', resp.url
        if URL_HOTEL == req['req']['url']:
            print 'hotel url:', resp.url
        else:
            print 'hotel param url:', resp.url
    
    def parse_hotel_params(self, req, data):
        pat = re.compile(r"SelectPass\('(.*)'")
        res = pat.findall(data)[0]
        self.user_datas['SelectPass'] = res.replace('$', ',')
        print 'res', res

    def convert_hotel_json(self, req, data):
        pattern = re.compile(r'FullHotelInfo.*?:(.*?)\} *?\*\$PPP', re.S)
        data_raw = pattern.findall(data)[0]
        try:
            # print data, '==='
            infoall = json.loads(data_raw)
        except:
            data_raw = data_raw.replace('"', "@").replace("'", '"').replace("@", "'")
            # print data, '==='
            infoall = json.loads(data_raw)
        # open('data.json', 'w').write(json.dumps(infoall))
        return infoall
    
    def parse_hotel(self, req, data):
        
        return hotellist_parse.parse_hotelList_hotel(data)
        # if URL_HOTEL == req['req']['url']:
        #     res = [r.get('MRL', None) for r in data]
        #     return res
        # else:
        #     return []
    
    def parse_room(self, req, data):
        
        return hotellist_parse.parse_hotelList_room(data, self.user_datas['mjcity_id'], self.user_datas['check_in'], self.user_datas['check_out'],
         self.user_datas['night'], self.user_datas['adult'], self.user_datas['currency_rates'])

if __name__ == '__main__':
    from mioji.common.task_info import Task
    task = Task()
    task.content = '50273&1&1&20170429'
    '10374&&布拉加###PT###BRA&&0&&1&&20170830'
    # task.extra['hotel'] = {'check_in':'20170123', 'nights':1, 'rooms':[{}] }
    # task.extra['hotel'] = {'check_in':'20170603', 'nights':1, 'rooms':[{'adult':1, 'child':3}]}
#     task.extra['hotel'] = {'check_in':'20170226', 'nights':1, 'rooms':[{'adult':1, 'child':2, 'child_age':[0, 6]}] * 2}
    spider = HotelListSpider(task)
    print spider.crawl(cache_config={"enable":True})
