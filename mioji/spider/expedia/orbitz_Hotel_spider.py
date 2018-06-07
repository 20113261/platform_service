# coding:utf-8

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
city_pat = re.compile(r'com/(.+)-Hotels')
sourceid_pat = re.compile('h(\d+)\.Hotel')
name_pat = re.compile(r'Hotels-(.*?)\.h')


class orbitzHotelSpider(BaseHotelSpider):
    source_type = 'orbitzHotel'
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room3'}
    }
    # 设置上不上线 unable
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'orbitzHotel': {'required': ['room']}
    }

    def first_params(self):
        return {'chkin': self.check_in_new, 'chkout': self.check_out_new}

    def setting(self):
        self.source = 'orbitz'
        self.task.content = self.task.content.replace('&&', '&')
        content = self.task.content
        task_list = content.split('&')
        self.task_list = task_list
        self.urltmp = task_list[0]

        sourceid = sourceid_pat.findall(self.urltmp)
        if len(sourceid) > 0:
            self.source_id = sourceid_pat.findall(self.urltmp)[0]
        else:
            raise parser_except.ParserException(parser_except.TASK_ERROR, "未获取到sourceid")

        try:
            self.city = city_pat.findall(self.urltmp)[0].replace('-', ' ')
        except:
            self.city = "NULL"
        self.dur = int(task_list[1])
        self.date1 = datetime.datetime(int(task_list[2][:4]), int(task_list[2][4:6]), int(task_list[2][6:]))
        self.check_in = str(datetime.datetime(int(task_list[2][:4]), int(task_list[2][4:6]), int(task_list[2][6:])))[:10]
        self.check_in_new = self.check_in[5:7] + "%2F" + self.check_in[8:10] + '%2F' + self.check_in[0:4]
        self.check_out = str(self.date1 + datetime.timedelta(self.dur))[0:10]
        self.check_out_new = self.check_out[5:7] + "%2F" + self.check_out[8:10] + '%2F' + self.check_out[0:4]
        self.children = 0
        self.room_info = self.task.ticket_info.get('room_info', [])
        self.occ = self.task.ticket_info.get('occ', 2)
        self.room_count = self.room_info[0].get('room_count', 1)
        self.json_url = 'https://www.orbitz.com/api/infosite/{0}/getOffers?token={1}&brandId={2}&isVip=false&chid=&chkin={3}&chkout={4}&ts={5}{6}'
        self.cid = self.task.ticket_info.get('cid', None)



if __name__ == '__main__':
    from mioji.common.task_info import Task
    task = Task()
    task.ticket_info = {'cid': 5}
    task.content = 'https://www.orbitz.com/Ceske-Budejovice-Hotels-Residence-U-Cerne-Veze.h4802435.Hotel-Information?&1&20180601'
    spider = orbitzHotelSpider()
    spider.task = task

    print spider.crawl()
    print spider.result
