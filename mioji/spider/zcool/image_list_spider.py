#!/usr/bin/env python
# -*- coding:utf-8 -*-
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
from copy import deepcopy
import json
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
import re
import time

driver = webdriver.PhantomJS()
base_url = "http://www.hellorf.com/image/search/{}?utm_source=search_zcool"
next_url = "http://www.hellorf.com/image/search/%E5%8C%97%E4%BA%AC?utm_source=search_zcool&page={}&=&"


class IMGSpider(Spider):
    source_type = 'zcool|image_list'
    targets = {
        'image': {},
    }
    old_spider_tag = {
        'zcool|image_list': {'required': ['image']}
    }

    def targets_request(self):

        task = self.task
        keywords = task.content

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['image'])
        def get_page_num():

            driver = webdriver.PhantomJS()
            # driver = webdriver.Chrome()
            username = '18569905260'
            password = 'Mioji2017'
            # driver.set_window_size(480, 760)
            driver.get(base_url.format(keywords))

            page = driver.page_source
            # print page

            begin = driver.find_element_by_xpath("//div[@id='image_login']").text
            print begin

            cookie1 = driver.get_cookies()
            # 根据xpath获取登录按钮
            driver.find_element_by_id("topnav_login").click()

            # 睡两秒后
            sleep(2)
            driver.find_element_by_name("username").send_keys(username)

            driver.find_element_by_name("password").send_keys(password)

            driver.find_element_by_xpath("//button[@class='zcool-button-primary']").click()

            sleep(2)
            result = driver.find_element_by_xpath("//div[@id='image_login']").text
            print result

            cookie2 = driver.get_cookies()
            li = []
            for i in cookie2:
                value = i.get('value')
                if len(value) > 100:
                    cookie2 = value
                    li.append(cookie2)
            cookie2 = 'hf_login_v1=' + li[0]

            return {'req': {'url': base_url.format(keywords),
                            'headers': {'Cookie': cookie2}},
                    'data': {'content_type': 'html'},
                    'user_handler': [self.parse_page_num]
                    }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=['image'])
        def get_all_page():
            li = []
            n = 1
            while n < self.total_num:
                n += 1
                li.append({'req': {'url': next_url.format(n)},
                           'data': {'content_type': 'html'},
                           })
            return li

        yield get_page_num
        yield get_all_page

    def parse_page_num(self, req, data):
        root = data

    def parse_image(self, req, data):
        # 可以通过request binding=[]指定解析方法
        # 判断是否登录
        user_message = data.xpath("//div[@class='topRight r']/ul//a/text()")[3]
        if "五环比四环少一环" in user_message:
            print "登陆成功"
        else:
            print "没有登录"

        img_list = []
        item = {}
        total_num = data.xpath("//div[@class='search-pagenav']/span[1]/text()")[0]
        total_num = total_num[4:-2]
        self.total_num = int(total_num)
        div_list = data.xpath("//div[@class='imgItem maskWraper']")
        for div in div_list:
            item["thumbnail"] = div.xpath(".//div[@class='pic-box']/a/img/@data-original")[0]
            # item["img_detail_url"] = div.xpath(".//div[@class='pic-box']/a/@href")[0]
            item["id"] = div.xpath(".//div[@class='pic-box']/a/@data-id")[0]
            item["copyright"] = 1
            item["sname"] = 'zcool'
            item["stype"] = 'ListImg  Img'
            item["preview"] = "https://image.shutterstock.com/z/stock-photo-{}.jpg".format(item["id"])
            img_list.append(deepcopy(item))
        return img_list


if __name__ == '__main__':
    from mioji.common import spider

    # from mioji.common.utils import simple_get_socks_proxy_new
    # spider.slave_get_proxy = simple_get_socks_proxy_new

    # spider.pool.set_size(1)
    # spider.NEED_FLIP_LIMIT = False

    task = Task()
    task.content = '天津'
    imgspider = IMGSpider()
    imgspider.task = task
    imgspider.crawl()
    print imgspider.result['image']
    # for i in imgspider.result['image']:
    #     print i
    # print("================================" * 3)
    # print len(imgspider.result['image'])
    # print("================================" * 3)
