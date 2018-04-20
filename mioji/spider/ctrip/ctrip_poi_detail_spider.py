# -*- coding:utf-8 -*-

"""
@author: fengyufei
@date: 2018-01-31
@purpose: ctrip POI 景点，餐厅，购物 详情页
@update: 2018-02-28
"""
from mioji.common.logger import logger
from mioji.common import parser_except
from mioji.common.func_log import current_log_tag
from mioji.common.task_info import Task
from mioji.common.parser_except import PROXY_INVALID, PROXY_FORBIDDEN
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from lxml import html
import json
from collections import defaultdict
from urlparse import urljoin
import traceback
import re

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
}

class CtripPoiSpider(Spider):
    source_type = "CtripListInfo"

    # 抓取数据： 景点，餐厅，购物列表
    targets = {
        'POIdetail': {},
    }

    old_spider_tag = {
        'CtripPoi': {'required': ['POIdetail']}
    }
    page_type_dict={'sight':'Sight','food':'Restaurant','shopping':'Shopping'}

    def __init__(self):
        super(CtripPoiSpider, self).__init__()
        self.header = headers
        self.map_info = ""
        self.tag = ""
        self.traffic = ''
        self.been = ''
        self.want = ''
        self.poi_id =''

    def targets_request(self):
        tid = 'demo'
        used_times =3
        self.tag = self.task.content.split('/')[-3]
        self.poi_id = self.task.content.split('.html')[0].split('/')[-1]

        @request(retry_count=5,proxy_type=PROXY_REQ)
        def traffic_info():
            url = self.task.content.split('.html')[0]+ '-traffic.html'
            return {
                    'req': {'url': url},
                    'data': {'content_type': 'html'},
                    'user_handler':[self.get_traffic_info]
                    }
        if self.tag == 'sight':
            yield traffic_info

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def map_info():
            url = self.task.content.split('.html')[0] + '-map.html'
            return {
                    'req':{'url': url},
                    'data':{'content_type': 'html'},
                    'user_handler':[self.get_map_info]
                }

        #if self.tag != 'food':
        yield map_info

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def ShowGowant():
            url = 'http://you.ctrip.com/Destinationsite/SharedComm/ShowGowant'
            return {
                    'req':{'url':url,'data':{'Resource':self.poi_id,'pageType':self.page_type_dict[self.tag]},'method':'post'},
                    'data':{'content_type': 'json'},
                    'user_handler':[self.get_gowant]
                    }
        yield ShowGowant

        @request(retry_count=5, binding=['POIdetail'], proxy_type=PROXY_REQ)
        def detail_info():
            url = self.task.content
            return {
                'req': {'url':url},
                'data': {'content_type': 'html'}
            }
        
        yield detail_info

    def get_gowant(self, req, data):
        self.been = data['WentTimes']
        self.want = data['WantTimes']

    def get_traffic_info(self, req, data):
        try:
            self.traffic = data.xpath('//div[@class="detailcon"]/div/p/text()')[0]
        except:
            pass

    def get_map_info(self, req, data):
        #self.map_info = re.findall('poiData:(.+})',html.tostring(data))[0]
        con = data.xpath('//script[not(@class or @type or @src)]')[0].text_content()
        self.map_info = re.findall('poiData:(.+})', con)[0]

    def data_parse(self,data):
        s= ''.join(''.join(''.join(data.split('\r')).split('\n')).split(' '))
        return s

    def parse_POIdetail(self, req, data):
        root = data
        try:
            nbp = root.xpath('//div[@class="cf"]/div')
            names = nbp[0]
            name = names.xpath('h1')[0].text_content()
            name_en =names.xpath('p/text()')[0].strip()
            
            tocounts = nbp[1].xpath('ul/li')
            beentocounts = int(self.been)
            plantocounts = int(self.want)

            grade = ''
            city = root.xpath('//div[@class="breadbar_v1 cf"]/ul/li')[-2].xpath('a/text()')[0]
            grades = root.xpath('//ul[@class="detailtop_r_info"]/li')
            try:
                grade = grades[0].xpath('span/b/text()')[0]
            except:
                print 'grade - none'
            
            commentcounts = ''
            try:
                commentcounts = grades[1].xpath('span[@class="pl_num"]/dfn/span/text()')[0]
            except:
                print 'commentcounts - none'

            image_url = ''
            image_num = ''
            try:
                image_url = root.xpath('//*[@id="detailCarousel"]/a/@href')[0]
                image_num = root.xpath('//*[@id="detailCarousel"]/a/text()')[0]
                image_num = re.findall('[0-9]+' ,image_num)[0]
            except:
                print 'image_url num - none'
            
            # -- grades detail
            try:
                title = []
                scores = []
                for de in root.xpath('//dl[@class="comment_show"]/*'):
                    if title == []:
                        title.append('all')
                    else:
                        title.append( de.xpath('//span[@class="l_title"]')[len(title)-1].text_content() )
                    scores.append( de.xpath('//span[@class="score"]')[0].text_content())
                grade_detail = dict(zip(title,scores))
            except:
                grade_detail= {}
            try:
                title = []
                scores = []
                for de in root.xpath('//ul[@class="cate_count"]/li'):
                    scores.append(de.xpath('a/span[1]/text()'))
                    title.append(de.xpath('a/span[2]/text()')[0])
                staff = dict(zip(title, scores))
            except:
                staff={}

            # ---- introduction
            descript = root.xpath('//div[@class="normalbox boxsight_v1"]/div')
            tips = ''
            for de in descript:
                try:
                    h = de.xpath('h2')[0].text_content()
                except:
                    continue
                if h == '特别提示' and self.tag != 'food':
                    try:
                        tips = self.data_parse(de.xpath('div[@class="toggle_l"]')[0].text_content())
                    except:
                        print 'tips - none'
                if h == '交通信息' and self.tag == 'shopping':
                    try:
                        self.traffic = self.data_parse(de.xpath('div[@class="toggle_l"]')[0].text_content())
                    except:
                        print 'traffic - none'

            introduction = ''
            try:
                if self.tag =='food':
                    introduction = html.tostring(root.xpath('//div[@itemprop="description"]')[0],encoding = 'utf-8')
                else:
                    introduction = html.tostring(root.xpath('//div[@itemprop="description"]')[1],encoding = 'utf-8')
            except Exception as e:
                print 'introduciton - none',e

            # ---- diff things 
            types = ''
            times = ''
            telephone = ''
            web = ''
            worktime = ''
            ticket= ''
            highlight=''

            if self.tag == 'sight' or self.tag == 'shopping':
                try:
                    busy = root.xpath("//ul[@class='s_sight_in_list']/li")
                    for b in busy:
                        fla = ''.join(b.xpath("span")[0].text_content().split(u'\xa0'))
                        res = ''.join(''.join(b.xpath('span')[1].text_content().split('\n')).split(' '))
                        if fla == '类型：':
                            types = '|'.join(b.xpath('span')[1].xpath('a/text()')) 
                        elif fla == '游玩时间：':
                            times = res
                        elif fla == '电话：':
                            telephone = res
                        elif fla == '官方网站：':
                            web = res
                except:
                    pass
                try:
                    tickets = root.xpath("//dl[@class='s_sight_in_list']")
                except:
                    pass
                try:
                    worktime =''.join(''.join(tickets[0].text_content().split('\n')).split(' '))
                except:
                    print 'worktime - none'
                try:
                    ticket =''.join(''.join(tickets[1].text_content().split('\n')).split(' '))
                except:
                    print 'ticket - none'

                try:
                    highlight = self.data_parse(root.xpath('//div[@class="detailcon bright_spot"]')[0].text_content())[1:]
                except :
                    pass

            price = ''

            if self.tag == 'food':
                try:
                    foo = root.xpath("//ul[@class='s_sight_in_list s_sight_noline cf']/li")
                    for fo in foo:
                        fla = fo.xpath('span')[0].text_content()
                        res = ''.join(''.join(fo.xpath('span')[1].text_content().split('\n')).split(' '))
                        if fla == '人 均：':
                            price = res
                        elif fla == '电 话：':
                            telephone = res
                        elif fla == '菜 系：':
                            types = '|'.join(fo.xpath('span')[1].xpath('dd/a/text()'))
                        elif fla == '营业时间：':
                            worktime = res
                except:
                    pass
                
                foo = root.xpath('//div[@class="detailcon"]')
                for fo in foo:   
                    try:
                        h= fo.xpath('h2/text()')[0]
                    except:
                        continue
                    if h == '交通':
                        try:
                            traff = fo.xpath('div')[0].text_content()
                            self.traffic = self.data_parse(traff)
                        except:
                            print 'traffic - none'
                    if h == '特别提示':
                        try:
                            tips = self.data_parse(fo.xpath('div')[0].text_content())
                        except:
                            print 'tips - none'
            mapp = json.loads(self.map_info.encode('utf-8'))
            address = mapp['address']
            map_info = ','.join([str(mapp['lat']),str(mapp['lng'])])

            temp = [name, name_en, beentocounts, plantocounts, city, grade, commentcounts, image_url, image_num, grade_detail, staff, introduction ,map_info,address,types,highlight,times,telephone,web,worktime, ticket,price, self.traffic,tips]

            #for i in temp:
            #    print i,'----end'
            #    print '==='

            return temp

        except Exception as e:
            print '----VON---',e
            logger.debug(
                current_log_tag() + '【{0}解析错误】{1}'.format(self.parse_POIlist.__name__, parser_except.PARSE_ERROR))



if __name__ == "__main__":
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    from mioji.common.pool import pool

    # spider.slave_get_proxy = simple_get_socks_proxy
    spider.NEED_FLIP_LIMIT = False
    pool.set_size(1024)
    task = Task()
    spider = CtripPoiSpider()
    task.content = 'http://you.ctrip.com/food/paris308/6976257.html'
    task.content = 'http://you.ctrip.com/shopping/paris308/1356289.html'
    #task.content = 'http://you.ctrip.com/sight/paris308/12908.html'

    #task.content = 'http://you.ctrip.com/food/paris308/8743378.html'
    #task.content = 'http://you.ctrip.com/sight/paris308/12565.html'
    #task.content = 'http://you.ctrip.com/shopping/paris308/1356291.html'

    #task.content ='http://you.ctrip.com/sight/montauk58103/1766759.html'
    #task.content = 'http://you.ctrip.com/shopping/centralvalley43112/1356615.html'
    #task.content = 'http://you.ctrip.com/sight/newyork248/133112.html'
    #task.content = 'http://you.ctrip.com/sight/otsu57061/110510.html'
    spider.task = task
    spider.crawl()
    print spider.code
    print spider.result
