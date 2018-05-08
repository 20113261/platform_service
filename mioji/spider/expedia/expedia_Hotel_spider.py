# coding:utf-8
import sys
sys.path.insert(0, '/Users/miojilx/Desktop/git/Spider/src/')
sys.path.insert(0, '/Users/miojilx/Desktop/git/slave_develop_new/workspace/spider/SpiderClient/bin')
from Hotel_Base_spider import BaseHotelSpider
import re
import datetime
from mioji.common import parser_except

num_pat = re.compile(r'(\d+)')
price_pat = re.compile(r'[0-9.,]+')
zh_pat = re.compile(ur'[\u4e00-\u9fa5]+')
en_pat = re.compile(r'[a-zA-Z ]+')
currency_pat = re.compile('[a-zA-Z]+')
pnum_pat = re.compile(r'(\d+)')
others_info_pat = re.compile(ur'（(.+)）')
city_pat = re.compile(r'cn/(.+)-Hotels')
city_pat1 = re.compile(r'hk/(.*?)-Hotels')
sourceid_pat = re.compile('h(\d+)\.Hotel')
name_pat = re.compile(r'Hotels-(.*?)\.h')


class expediaHotelSpider(BaseHotelSpider):

    source_type = 'expediaHotel'
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room3'}
    }
    # 设置上不上线 unable
    # unable = True
    # 关联  原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'expediaHotel': {'required': ['room']}
    }

    def setting(self):
        self.source = 'expedia'
        self.task.content = self.task.content.replace('&&', '&')
        content = self.task.content
        task_list = content.split('&')
        self.task_list = task_list
        self.urltmp = task_list[0]
        # https 才能成功
        if not self.urltmp.startswith('https'):
            self.urltmp = self.urltmp.replace('http', 'https')

        sourceid = sourceid_pat.findall(self.urltmp)
        if len(sourceid) > 0:
            self.source_id = sourceid_pat.findall(self.urltmp)[0]
        else:
            raise parser_except.ParserException(parser_except.TASK_ERROR,"未获取到sourceid")

        try:
            self.city = city_pat.findall(self.urltmp)[0].replace('-', ' ')
        except:
            self.city = "NULL"
        self.dur = int(task_list[1])
        self.date1 = datetime.datetime(int(task_list[2][:4]), int(task_list[2][4:6]), int(task_list[2][6:]))

        self.check_in = str(datetime.datetime(int(task_list[2][:4]), int(task_list[2][4:6]), int(task_list[2][6:])))[
                        :10]
        self.check_in_new = self.check_in[0:4] + "%2F" + self.check_in[5:7] + '%2F' + self.check_in[8:10]
        self.check_out = str(self.date1 + datetime.timedelta(self.dur))[0:10]
        self.check_out_new = self.check_out[0:4] + "%2F" + self.check_out[5:7] + '%2F' + self.check_out[8:10]
        self.children = 0
        self.room_info = self.task.ticket_info.get('room_info', [])
        self.occ = self.task.ticket_info.get('occ', 2)
        self.room_count = self.room_info[0].get('room_count', 1)

        # 需要注意参数顺序
        # 新的session requests；需要第一步的 cookies['MC1']
        self.json_url = 'https://www.expedia.com.hk/api/infosite/{0}/getOffers?token={1}&brandId={2}&countryId=0'\
                        + '&isVip=false&chid=&partnerName=&partnerPrice=0&partnerCurrency=&partnerTimestamp=0'\
                        + '&chkin={3}&chkout={4}&daysInFuture=&stayLength='\
                        + '{6}&ts={5}&tla={7}'

        self.cid = self.task.ticket_info.get('cid', None)

    def process_paging_url(self, req, data):
        #print data
        self.hotel_name = re.findall("<title>.*?\((.*?)\).*?</title>", data, re.S)[0]
        print self.hotel_name
        BaseHotelSpider.process_paging_url(self, req, data)
        # print self.browser.resp.cookies
        try:
            self.mc1 = self.browser.resp.cookies['MC1']
        except Exception as e:
            # res = guid = '12d0fa2ed6544078a8b92124bdcd904c'
            res = re.findall('guid = \'[a-z0-9]+?\'', data)
            print res
            if res:
                res = res[0].replace(' ', '').replace('guid', 'GUID').replace('\'', '').replace('\"', '')
                self.mc1 = res.encode()
            else:
                res = re.findall('guid = \"[a-z0-9]+?\"', data)
                if res:
                    res = res[0].replace(' ', '').replace('guid', 'GUID').replace('\'', '').replace('\"', '')
                    self.mc1 = res.encode()
                else:
                    # replace - to space
                    res = re.findall('\"guid\":\"[a-z0-9\-]+?\"', data)
                    if res:
                        res = res[0].replace(' ', '').replace('\"guid\":', 'GUID=').replace('\'', '').replace('\"', '')
                        self.mc1 = res.encode().replace('-', '')
                    else:
                        # replace - to space
                        res = re.findall("_guid = \"[a-z0-9\-]+?\"", data)
                        if res:
                            res = res[0].replace(' ', '').replace('_guid', 'GUID').replace('\'', '').replace('\"', '')
                            self.mc1 = res.encode().replace('-', '')
                        else:
                            raise parser_except.ParserException(parser_except.TASK_ERROR,"未获取到MC1")
            print self.mc1
            print '在静态数据中抓取到MC1'
        print '获取到MC1:', self.mc1


    def api_newsession(self):
        return True



if __name__ == '__main__':
    from mioji.common.task_info import Task
    # from mioji.common.utils import simple_get_socks_proxy
    # from mioji.common import spider
    # spider.slave_get_proxy = simple_get_socks_proxy
    
    task = Task()
    task.ticket_info = {"count": 6, "room_info": [{"occ": 2, "num": 1, "room_count": 6}], "room_count": 6, "uid": "o949kgym5a115c432cb93179be19oy2v", "cid": "10004", "env_name": "online", "occ": 2, "num": 6, "qid": "1511150042274", "pay_method": "mioji", "md5": "a7abd666b2d5690e0df1414908bbf57e"}
    # task.content = 'http://www.expedia.com.hk/cn/Yokohama-Hotels-Sotetsu-Fresa-Inn-Yokohama-Totsuka.h4482717.Hotel-Information?&7&20171010'
    #task.content = 'https://www.expedia.com.hk/cn/Yokohama-Hotels-Yokohama-Royal-Park-Hotel.h15450.Hotel-Information?&1&20171214'
    # task.content = "http://www.expedia.com.hk/cn/Sapporo-Hotels-La'gent-Stay-Sapporo-Oodori-Hokkaido.h15110395.Hotel-Information?&2&20171202"
    # task.content = "https://www.expedia.com.hk/cn/Hotels-Hotel-Home-Florence.h1166901.Hotel-Information?&3&20180628"
    # task.content = "https://www.expedia.com.hk/h2039863.Hotel-Information?&1&20180119"
    # task.content = "https://www.expedia.com.hk/cn/Hotels-Holiday-Inn-Vancouver-Airport.h63501.Hotel-Information?&1&20180210"
    # task.content = 'https://www.expedia.com.hk/cn/Hotels-Residence-Inn-By-Marriott-Montreal-Downtown.h65939.Hotel-Information?&1&20171205'
    task.content = 'https://www.expedia.com.hk/cn/Luxor-Hotels-Eatabe-Luxor-Hotel.h525107.Hotel-Information?&2&20180218'
    task.source = 'expedia'
    spider = expediaHotelSpider()
    spider.task = task
    print spider.crawl()
    print spider.result
    

    
