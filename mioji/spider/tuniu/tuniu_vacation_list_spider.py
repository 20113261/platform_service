#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from bs4 import BeautifulSoup
from mioji.common.class_common import Room
from lxml import etree
from mioji.common import spider
from copy import deepcopy


spider.pool.set_size(2014)
spider.NEED_FLIP_LIMIT = False


class TuniuSpider(Spider):

    source_type = 'tuniu|vacation_list'

    targets = {
    'list':{},
    }
    old_spider_tag = {
        'tuniu|vacation_list': {'required': ['list']}
            }



    def targets_request(self):
        base_url1 = 'http://s.tuniu.com/search_complex/around-{}-0-{}'
        next_url1 = 'http://s.tuniu.com/search_complex/around-{}-0-{}/{}'

        base_url2 = 'http://s.tuniu.com/search_complex/tours-{}-0-{}/{}'
        next_url2 = 'http://s.tuniu.com/search_complex/tours-{}-0-{}/{}/{}'

        ticket_info = self.task.ticket_info['vacation_info']
        self.id = ticket_info["dept_info"]["id"]
        self.name = ticket_info["dest_info"]["name"]  # 目的地名称
        self.dept_name = ticket_info["dept_info"]["name"]  # 出发地名称
        self.name_en = ticket_info["dept_info"]["name_en"]  # 出发地英文名
        self.vacation_type = ticket_info["vacation_type"]
        self.dept_name_id = ticket_info["dept_info"]["id"].replace('list-l', '') # 出发地名称ID
        self.name_id = ticket_info["dest_info"]["id"]  # 目的地名称ID
        if self.vacation_type == "around":
            @request(retry_count=3, proxy_type=PROXY_REQ, binding=['list'])
            def get_page_num():
                # print(base_url1.format(self.name_en, self.name))
                return {'req': {'url': base_url1.format(self.name_en, self.name)},
                    'data':{'content_type': 'html'},
                    'user_handler':[self.parse_page_num]
                    }

            @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=['list'])
            def get_all_page():
                li = []
                n = 1
                while n < self.total_num:
                    n += 1
                    li.append({'req': {'url': next_url1.format(self.name_en, self.name,n)},
                        'data':{'content_type':'html'},
                            })
                return li

            yield get_page_num
            if self.total_num > 1:
                yield get_all_page
        else:
            @request(retry_count=3, proxy_type=PROXY_REQ, binding=['list'])
            def get_page_num():
                return {'req': {'url': base_url2.format(self.name_en, self.name, self.id)},
                        'data': {'content_type': 'html'},
                        'user_handler': [self.parse_page_num]
                        }

            @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=['list'])
            def get_all_page():
                li = []
                n = 1
                # while n < 3:
                while n < self.total_num:
                    n += 1
                    li.append({'req': {'url': next_url2.format(self.name_en, self.name,self.id, n)},
                            'data':{'content_type':'html'},
                                })
                return li

            yield get_page_num
            if self.total_num > 1:
                yield get_all_page



    def parse_page_num(self,req,data):
        root = data


    """
       {"id": "18829225",
        "search_dept_city_id": "1",
        "search_dept_city": "北京",
        "search_dest_city_id": "",
        "search_dest_city": "意大利",
        "dept_city": "北京",
        "first_image": "列表页传入",
        "url": "http://vacations.ctrip.com/grouptravel/p18829225s1.html",
        "brand": "列表页出传入"
        }
    """
    def parse_list(self, req, data):
        tuniu_list = []
        item = {}
        total_num = data.xpath("//div[@class='page-bottom']/a/text()")
        if len(total_num) == 1:
            total_num = total_num[0]
        elif len(total_num) > 1:
            total_num = total_num[-2]
        self.total_num = int(total_num)
        li_list = data.xpath("//ul[@class='thebox clearfix zizhubox']/li")
        if not li_list:
            li_list = data.xpath("//ul[@class='thebox clearfix']/li")
        for li in li_list:
            try:
                tuniu_type = li.xpath(".//dd[@class='tqs']/span[@class='brand']/span/text()")[0]
            except Exception:
                tuniu_type = 'type None'
            if tuniu_type != '牛人专线' and tuniu_type != '途牛国旅':
                item['first_image'] = 'http:' + li.xpath(".//div[@class='img']/img/@data-src")[0]
                productId = li.xpath(".//a[@class='clearfix']/@m")[0]
                item['id'] = productId.split('_')[-1]
                # item['source_type'] = "Tuniu | vacation_list"
                item['url'] = 'http:' + li.xpath(".//a[@class='clearfix']/@href")[0]
                # item['title'] = li.xpath(".//p[@class='title']/span[@class='main-tit']/@name")[0]
                # dept_city_list = li.xpath(".//p[@class='subtitle']/span/text()")
                # desc = ''
                # for dept_city in dept_city_list:
                #     desc += dept_city
                # number = desc.count("|")
                # if number == 2:
                #     index = desc.rfind("|")
                #     desc = desc[:index]
                # else:
                #     desc = desc
                if self.vacation_type == "around":
                    item["dept_city"] = "0"
                else:
                    dept_city = li.xpath(".//p[@class='subtitle']/span/text()")[0][:2]
                    item["dept_city"] = dept_city

                # search_dept_city: str搜索城市
                # search_dest_city ：str搜索目的地城市
                item["search_dept_city"] = self.dept_name
                item["search_dest_city"] = self.name
                item["search_dept_city_id"] = self.dept_name_id
                item["search_dest_city_id"] = self.name_id
                # item['minimum_money'] = li.xpath(".//div[@class='tnPrice']/em/text()")[0]
                # item['supplier'] = ""
                # try:
                #     item['satisfied'] = li.xpath(".//div[@class='comment-satNum']/span/i/text()")[0] + '%'
                # except Exception:
                #     item['satisfied'] = 'new product'

                # try:
                #     item['supplier_category'] = li.xpath(".//dd[@class='tqs']/span[@class='brand']/label/text()")[0][
                #                                 :-1]
                # except Exception:
                #     item['supplier_category'] = 'supplier_category None'
                try:
                    item['brand'] = li.xpath(".//dd[@class='tqs']/span[@class='brand']/span/text()")[0]
                except Exception:
                    item['brand'] = 'supplier None'
                # try:
                #     item['highlights'] = li.xpath(".//span[@class='sub-tuijian']/text()")[0]
                #     if item['highlights'][0] == '|':
                #         item['highlights'] = item['highlights'][1:]
                # except Exception:
                #     item['highlights'] = 'highlights None'
                # try:
                #     item['contain_view'] = li.xpath(".//span[@class='overview-scenery']/text()")[0]
                # except Exception:
                #     item['contain_view'] = 'contain_view None'
                # try:
                #     level = li.xpath(".//span[@class='mytip lev-star']/@style")[0]
                #     if level == 'width: 30px;':
                #         level = '3xing'
                #     elif level == 'width: 42px;':
                #         level = '4xing'
                #     elif level == 'width: 54px;':
                #         level = '5xing'
                #     item['level'] = level
                # except Exception:
                #     item['level'] = 'level None'
                tuniu_list.append(deepcopy(item))
            else:
                continue
        return tuniu_list



if __name__ == '__main__':
    from mioji.common.task_info import Task
    # from mioji.common.utils import simple_get_socks_proxy, httpset_debug
    # spider.slave_get_proxy = simple_get_socks_proxy

    list_place = ['普吉岛', '巴厘岛', '土耳其']
    for each in list_place:
        spider = TuniuSpider()
        task = Task()
        spider.task = task
        task.ticket_info['vacation_info'] = {
        #出发地
        "dept_info":
        {
            "id": "list-l1602",  #"string 出发地id",
            "name": "南京",  # "string出发地名称",
            "name_en": "nj",  # "string出发地英文名",
        },
        # 目的地
        "dest_info":
        {
            "id": "",  # "string 目的地id",
            "name": each,  # "string目的地名称",
            "name_en":  "",  # "string目的地英文名",
        },
        "vacation_type":  "grouptravel"  #"around" "grouptravel"
        }

        spider.crawl()
        print spider.result
        break

    # print json.dumps(spider.result, ensure_ascii=False)



