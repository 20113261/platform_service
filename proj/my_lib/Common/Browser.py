#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/9 上午10:27
# @Author  : Hou Rong
# @Site    : 
# @File    : Browser.py
# @Software: PyCharm
import requests
import time
import urlparse
import httplib
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent
from requests import ConnectionError, ConnectTimeout
from requests.adapters import SSLError, ProxyError

httplib.HTTPConnection.debuglevel = 1
requests.packages.urllib3.disable_warnings()


class MySession(requests.Session):
    def __init__(self, need_proxies=True, auto_update_host=True):
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
        self.auto_update_host = auto_update_host

    def send(self, request, **kwargs):
        if self.auto_update_host:
            if 'Host' not in request.headers:
                request.headers['Host'] = urlparse.urlparse(request.url).netloc

        return super(MySession, self).send(request, **kwargs)

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
        if not exc_type:
            self.update_proxy(0)
        elif exc_type in (SSLError, ProxyError):
            self.update_proxy(22)
        elif exc_type in (ConnectionError, ConnectTimeout):
            self.update_proxy(23)


if __name__ == '__main__':
    # with MySession() as session:
    #     page = session.get('http://www.baidu.com')
    #     print page.text

    # with MySession() as session:
    #     page = session.get(
    #         'http://www.tripadvisor.cn/ShowUrl?&excludeFromVS=false&odc=BusinessListingsUrl&d=10006331&url=0')
    #     print page.url

    with MySession(need_proxies=False) as session:
        # session.headers.update({
        #     'Host': 'www.tripadvisor.cn'
        # })
        page = session.get(
            'http://www.tripadvisor.cn/ShowUrl?&excludeFromVS=false&odc=BusinessListingsUrl&d=100368&url=1')
        print page.url
