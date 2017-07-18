#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/9 上午10:27
# @Author  : Hou Rong
# @Site    : 
# @File    : Browser.py
# @Software: PyCharm
import requests
import time
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent


class MySession(requests.Session):
    def __init__(self, need_proxies=True):
        self.start = time.time()
        super(MySession, self).__init__()
        headers = {
            'User-agent': GetUserAgent()
        }
        self.headers = headers

        self.p_r_o_x_y = None
        if need_proxies:
            self.change_proxies()

        self.verify = False

    def change_proxies(self):
        self.p_r_o_x_y = get_proxy(source="Platform")
        proxies = {
            'http': 'socks5://' + self.p_r_o_x_y,
            'https': 'socks5://' + self.p_r_o_x_y
        }
        self.proxies = proxies

    def update_proxy(self, error_code):
        update_proxy('Platform', self.p_r_o_x_y or 'NULL', time.time() - self.start, error_code)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    # with MySession() as session:
    #     page = session.get('http://www.baidu.com')
    #     print page.text

    with MySession() as session:
        page = session.get(
            'http://www.tripadvisor.cn/ShowUrl?&excludeFromVS=false&odc=BusinessListingsUrl&d=10006331&url=0')
        print page.url
