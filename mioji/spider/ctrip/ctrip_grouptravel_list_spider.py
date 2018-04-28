#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import sys
import re
import requests
import urllib
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from bs4 import BeautifulSoup
from lxml import etree
from mioji.common import spider
spider.pool.set_size(2014)
spider.NEED_FLIP_LIMIT = False
reload(sys)
sys.setdefaultencoding("utf-8")


class CitripGrouptravelListSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'ctrip|vacation_list'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        'list': {},
        # 例行需指定数据版本：InsertHotel_room4
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'ctrip|vacation_list': {'required': ['list']}
    }

    def targets_request(self):
        # u can get task info from self.task
        # task = self.task
        task_info = self.task.ticket_info['vacation_info']
        dept_name = task_info['dept_info']['name_en']
        dest_name = task_info['dest_info']['name_en']
        dest_id = task_info['dest_info']['id']
        vacation_type = task_info['vacation_type']
        base_url = "http://vacations.ctrip.com/grouptravel/startcity/{}".format(dept_name)
        # search_url = 'http://vacations.ctrip.com/tours/d-bali-438/grouptravel/dc1n1'
        # search_url = "http://vacations.ctrip.com/tours/d-unitedstates-100047/around/dc347"
        # search_url = "http://vacations.ctrip.com/tours/d-phuket-364/grouptravel/dc144"
        search_url = "http://vacations.ctrip.com/tours/d-{0}-{1}/{2}/".format(dest_name, dest_id, vacation_type)
        # search_url = "http://vacations.ctrip.com/tours/d-paris-308/around/dc250"
        tid = 0
        used_times = 0

        @request(retry_count=3, proxy_type=PROXY_REQ, store_page_name="base_request_{}_{}".format(tid, used_times))
        def base_request():
            return {'req': {'url': base_url},
                    # 'data': {'content_type': 'html'},
                    }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_list, store_page_name="first_request_{}_{}".format(tid, used_times))
        def first_request():
            return {'req': {'url': search_url},
                    # 'data': {'content_type': 'html'},
                    'user_handler': [self.get_total_page, self.get_api_info]
                    }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_list, async=True, store_page_name="second_request_{}_{}".format(tid, used_times))
        def second_request():
            total_page = self.total_page
            list_a = []
            if total_page >= 30:
                for page in range(2, 31):
                    list_a.append({'req': {'url': self.next_url + '/' + 'p' + str(page)},
                                   'user_handler': [self.get_api_info]
                                   })
                return list_a
            else:
                for page in range(2, total_page+1):
                    list_a.append({'req': {'url': self.next_url + '/' + 'p' + str(page)},
                                   'user_handler': [self.get_api_info]
                                   })
                return list_a

        yield base_request
        yield first_request
        if self.total_page >= 2:
            yield second_request

    def get_api_info(self, req, data):
        soup = BeautifulSoup(data, 'lxml')
        node3_list = soup.find_all('div', {'class': 'main_mod'})
        id_list = []
        pic_list = []
        highlight = []
        dept_id_list = []
        dept_list = []
        supplier4 = []
        url = "http://vacations.ctrip.com/tour-mainsite-vacations/api/product"
        for node in node3_list:
            info = node.get('data-params')
            info2 = json.loads(info)
            id_list.append(info2['Id'])
        # print(self.task.ticket_info)
        Did = self.task.ticket_info['vacation_info']['dept_info']['id']
        id_new_list = []
        for id in id_list:
            id_new_list.append({"Id": id, "Bu": "GT", "Did": int(Did)})
        payload = {'params': id_new_list}
        payload = urllib.urlencode(payload)
        proxies = dict()
        # proxy_info = requests.get(
        #     "http://10.10.32.22:48200/?type=px001&qid=0&query={%22req%22:%20[{%22source%22:%20%22ctripFlight%22,%20%22num%22:%201,%20%22type%22:%20%22verify%22,%20%22ip_type%22:%20%22test%22}]}&ptid=test&uid=test&tid=tid&ccy=spider_test").content
        # proxy = json.loads(proxy_info)['resp'][0]['ips'][0]['inner_ip']
        proxy_info = requests.get("http://10.10.239.46:8087/proxy?source=pricelineFlight&user=crawler&passwd=spidermiaoji2014").content
        # proxies['socks'] = "socks5://" + proxy.encode('utf-8')
        proxies['socks'] = "socks5://" + proxy_info.encode('utf-8')
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.323132 Safari/537.36",
            'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Cache-Control': "no-cache",
            'Postman-Token': "77e0e6b7-b7c3-6ef1-de14-8686f2d0a844"
        }
        response = requests.post(url, data=payload, headers=headers, proxies=proxies).content
        response = json.loads(response)
        try:
            for resp in response:
                pic = resp.get('ImageUrl')
                if pic:
                    pic = pic.replace("_C_125_70", "")
                    pic_list.append(pic)
                else:
                    pic_list.append("")
                dept_id_list.append(resp.get('DepartureCityId'))
                dept_list.append(resp.get('DepartureCityName'))
                supplier4.append(resp.get('ProviderFullName'))
                if resp.get('Tags'):
                    h_list = []
                    for resp2 in resp.get('Tags'):
                        tag = resp2.get('Name')
                        if tag != "":
                            h_list.append(tag)
                        else:
                            tag2 = "免费WIFI"
                            h_list.append(tag2)
                    highlight.append(h_list)
                else:
                    h_list = []
                    highlight.append(h_list)
        except Exception as e:
            print(e)
        self.pic_list = pic_list
        self.highlight = highlight
        self.dept_id_list = dept_id_list
        self.dept_list = dept_list
        self.supplier = supplier4

    def get_total_page(self, req, data):
        html_obj = etree.HTML(data)
        page_list = html_obj.xpath("//div[@id='_pg']/a/text()")
        self.total_page = int(page_list[-2])
        self.next_url = req['resp'].url

    def parse_list(self, req, data):
        # 可以通过request binding=[]指定解析方法
        travel = []
        html_obj = etree.HTML(data)
        soup = BeautifulSoup(data, 'lxml')
        node_list = soup.find_all('div', {'class': 'product_pic'})
        link_list = []
        for node in node_list:
            link = node.find('a').get('href')
            link = "http:" + link
            link_list.append(link)
        node3_list = soup.find_all('div', {'class': 'main_mod'})
        id_list = []
        for node in node3_list:
            info = node.get('data-params')
            info2 = json.loads(info)
            id_list.append(info2['Id'])
        title_list = html_obj.xpath("//div[@class='product_main']/h2[@class='product_title']/a/text()")
        # print(len(title_list))
        days_list = []
        for title in title_list:
            title2 = re.search(u"(\w+)日(\w+)晚", title)
            title3 = re.search(u"(\w+)日", title)
            if title2:
                days1 = title2.group(1)
                days2 = title2.group(2)
                day_str = days1 + "日" + days2 + "晚"
                days_list.append(day_str)
            elif title3:
                days = title3.group(1)
                day_str = days + "日"
                days_list.append(day_str)
            else:
                days = 'None'
                days_list.append(days)
        grade_list = html_obj.xpath("//div[@class='product_main']/h2/a")
        star_list = []
        for grade in grade_list:
            span = grade.xpath("./span/@data-star")
            if span is None:
                star = 'null'
                star_list.append(star)
            else:
                star_list.append(span[0])
        # print(star_list)
        supplier_list = html_obj.xpath("//div[@class='product_main']/div/div/div/p[@class='product_retail']/text()")
        supplier_str = ""
        for supplier in supplier_list:
            supplier_str += supplier
        # print(supplier_str)
        # print(len(supplier_list))
        supplier_list2 = supplier_str.split("：")
        supplier_list2.remove(supplier_list2[0])
        supplier_list3 = []
        for supplier2 in supplier_list2:
            supplier2 = supplier2.replace("供应商", "").replace("零售商", "")
            supplier_list3.append(supplier2)
        # print(len(supplier_list2))

        product_list = []
        for product in zip(link_list, id_list, supplier_list3, self.pic_list, self.dept_list, self.dept_id_list, self.supplier, self.highlight):
            product_list.append(product)
        filter_list = filter(lambda x: '携程自营' not in x, product_list)
        # print(filter_list)
        for product in filter_list:
            source_type = "Ctrip|vacation_list"
            search_dept_city = self.task.ticket_info['vacation_info']['dept_info']['name']
            search_dest_city = self.task.ticket_info['vacation_info']['dest_info']['name']
            # dest_id = self.task.ticket_info['vacation']['dest_info']['id']
            url = product[0]
            pid_3rd = product[1]
            # detail_url = product[0]
            # pd_id = product[1]
            # title = product[2]
            brand = product[2]
            first_image = product[3]
            dept_city = product[4]
            dept_id = product[5]
            # days = product[4]
            # star = product[5]
            # first_pic = product[6]
            highlight = product[7]
            supplier = product[6]
            p_tuple = dict(source_type=source_type, search_dept_city=search_dept_city, search_dest_city=search_dest_city,
                           dept_city=dept_city, dept_id=str(dept_id), url=url, pid_3rd=pid_3rd, brand=brand, first_image=first_image,
                           supplier=supplier, highlight=highlight)
            travel.append(p_tuple)
            # with open("beijing2turkey.json", "a") as f:
            #     f.write(json.dumps(p_tuple, ensure_ascii=False) + "\n")
        return travel

    def parse_room(self, req, data):
        return []


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug

    spider.slave_get_proxy = simple_get_socks_proxy

    spider = CitripGrouptravelListSpider()
    task = Task()
    task.ticket_info['vacation_info'] = {
        "dept_info": {
            "id": "1",
            "name": "北京",
            "name_en": "Beijing"},
        "dest_info": {
            "id": "308",
            "name": "巴黎",
            "name_en": "tour"},
        "vacation_type": "grouptravel"
    }
    spider.task = task

    # print spider.crawl()
    spider.crawl()
    print json.dumps(spider.result, ensure_ascii=False)
