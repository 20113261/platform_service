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
import json
import redis
import time
import datetime
from common.common import get_proxy, update_proxy
from util.UserAgent import GetUserAgent
from requests import ConnectionError, ConnectTimeout
from requests.adapters import SSLError, ProxyError
from proj.my_lib.Common import RespStore
from proj.my_lib.logger import get_logger

logger = get_logger('Browser')
httplib.HTTPConnection.debuglevel = 1
requests.packages.urllib3.disable_warnings()

ip_saver_pool = redis.ConnectionPool(host='10.10.213.148', port=6379, db=0, max_connections=1)


class MySession(requests.Session):
    def __init__(self, need_proxies=True, auto_update_host=True, need_cache=False):
        self.start = time.time()
        super(MySession, self).__init__()
        headers = {
            'User-agent': GetUserAgent()
        }
        self.headers = headers
        self.verify = False
        self.auto_update_host = auto_update_host
        self.md5 = []
        self.md5_resp = {}
        self.need_cache = need_cache
        self.cache_expire_time = 2592000  # 60 * 60 * 24 * 30

        self.p_r_o_x_y = None
        if need_proxies:
            self.change_proxies()

    def send(self, request, **kwargs):
        if self.auto_update_host:
            if 'Host' not in request.headers:
                request.headers['Host'] = urlparse.urlparse(request.url).netloc

        if self.need_cache:
            # get cache key
            req = {}
            for k, v in request.__dict__.items():
                if k in ['method', 'url', 'params', 'data', 'auth', 'json']:
                    req[k] = v

            # get cache
            md5 = RespStore.calculate_md5(req)
            self.md5.append(md5)
            if not RespStore.has_cache(md5):
                resp = None
            else:
                resp = RespStore.get_by_md5(md5, self.cache_expire_time)

            # check cache
            if resp:
                logger.debug('[使用缓存][ {0} ]'.format(json.dumps(req, sort_keys=True)))
                try:
                    # cache can be used
                    if not self.cache_check(req, resp):
                        logger.debug('[缓存未通过检测][ {0} ]'.format(json.dumps(req, sort_keys=True)))
                except Exception:
                    logger.warning('cache error')

            # need crawl
            if not resp:
                resp = super(MySession, self).send(request, **kwargs)
                self.md5_resp[md5] = resp
        else:
            resp = super(MySession, self).send(request, **kwargs)

        return resp

    def cache_check(self, req, resp):
        return True

    def get_real_ip(self, targets):
        host, key = targets
        try:
            start = time.time()
            ip_page = self.get(host, proxies=self.proxies, timeout=10)
            out_ip = json.loads(ip_page.text)[key]
            logger.debug("[获取公网 ip 地址][ip: {0}][耗时: {1}]".format(out_ip, time.time() - start))
        except Exception as e:
            logger.exception("[获取公网 ip 地址失败]", exc_info=e)
            return None
        return out_ip

    def change_proxies(self):
        self.p_r_o_x_y = get_proxy(source="Platform")
        proxies = {
            'http': 'socks5://' + self.p_r_o_x_y,
            'https': 'socks5://' + self.p_r_o_x_y
        }
        self.proxies = proxies

        # 缓存属性
        need_cache = self.need_cache

        # ip report get real ip address
        self.need_cache = False

        out_ip = None
        for targets in [('http://httpbin.org/ip', 'origin'), ('https://api.ipify.org?format=json', 'ip')]:
            out_ip = self.get_real_ip(targets)
            if out_ip:
                break

        if out_ip:
            try:
                r = redis.Redis(connection_pool=ip_saver_pool)
                r.incr(datetime.datetime.now().strftime("ip_%Y_%m_%d_{0}".format(out_ip)))
            except Exception as e:
                logger.exception("[ip 地址入 redis 失败]", exc_info=e)
                return False

        self.need_cache = need_cache
        return True

    def update_proxy(self, error_code):
        try:
            update_proxy('Platform', self.p_r_o_x_y or 'NULL', time.time() - self.start, error_code)
        except Exception:
            pass

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

        if self.need_cache:
            # store page check
            if exc_type is None:
                # save any not stored cache
                for k, v in self.md5_resp.items():
                    if not RespStore.has_cache(k):
                        logger.info('[保存缓存][md5: {}]'.format(k))
                        RespStore.put_by_md5(k, v)
            else:
                # don't store page or delete the page
                for each_md5 in self.md5:
                    if RespStore.has_cache(each_md5):
                        logger.info('[删除缓存][md5: {}]'.format(each_md5))
                        RespStore.delete_cache(each_md5)


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
            'http://bbs.qyer.com/thread-1384644-1.html')
        print(page.url)
        print(page.text)
        # raise Exception()
