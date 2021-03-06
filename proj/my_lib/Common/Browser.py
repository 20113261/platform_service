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
import proj.my_lib.Common.RespStore
import proj.my_lib.logger
import random
from mioji.common.user_agent_list import random_useragent
# from util.UserAgent import GetUserAgent
from requests import ConnectionError, ConnectTimeout
from requests.adapters import SSLError, ProxyError
from proj.my_lib.Common.Utils import try3times
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Utils import retry
from proj.my_lib.Common.ProxyPool import ProxyPool

# from proj.my_lib.Common import RespStore
# from proj.my_lib.logger import get_logger

# httplib.HTTPConnection._http_vsn = 10
# httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'

logger = proj.my_lib.logger.get_logger('Browser')
# httplib.HTTPConnection.debuglevel = 1
requests.packages.urllib3.disable_warnings()

source_list = ['turbojetsail', 'elongHotel', 'ctripHotel', 'tongchengApiHotel', 'expediaHotel', 'bookingHotel',
               'HotelsHotel', 'biyiHotel', 'HotelclubHotel', 'venereHotel', 'agodaHotel', 'ebookersHotel', 'ihgHotel',
               'marriottHotel', 'amomaHotel', 'hrsHotel', 'HoteltravelHotel', 'accorHotel', 'travelocityHotel',
               'orbitzHotel', 'cheapticketsHotel', 'miojiHotel', 'hotwireHotel', 'kempinskiHotel', 'whgHotelsHotel',
               'starwoodHotelsHotel', 'hostelworldHotel', 'HotelbedsApiHotel', 'haoqiaoApiHotel', 'innstantApiHotel',
               'touricoApiHotel', 'gtaApiHotel', 'daolvApiHotel', 'jacApiHotel', 'mikiApiHotel', 'dotwApiHotel',
               'tripadvisorHotel', 'hiltonHotel', 'yundijieHotel', 'elongFlight', 'ryanairFlight', 'ctripFlight',
               'jijitongFlight', 'tongchengFlight', 'feiquanqiuRoundFlight', 'ceairFlight', 'csairFlight',
               'expediaMultiFlight', 'smartfaresFlight', 'easyjetFlight', 'wegoFlight', 'vuelingFlight',
               'ufeifanFlight', 'youzhanHotel', 'airberlinFlight', 'huifeeFlight', 'tripstaFlight', 'ebookersFlight',
               'mangoFlight', 'cheapoairFlight', 'airtickets24Flight', 'airkxFlight', 'pricelineFlight', 'kopuFlight',
               'airchinaFlight', 'hnairFlight', 'britishairFlight', 'airfranceRoundFlight', 'travelocityFlight',
               'orbitzFlight', 'studentuniverseFlight', 'cheapticketsFlight', 'lufthansaFlight', 'omegaFlight',
               'travelfusionFlight', 'emiratesFlight', 'aeroflotFlight', 'aliFlight', 'onetravelFlight', 'qunarFlight',
               'qatarFlight', 'austrianAirlinesFlight', 'budgetairFlight', 'travelgenioFlight', 'miojiFlight',
               'skyscannerFlight', 'cheapairFlight', 'jintongApiFlight', 'mytripFlight', 'cleartripFlight',
               'zujiFlight', 'gotogateFlight', 'yinlingApiFlight', 'zailushangApiMultiFlight', 'edreamsRoundFlight',
               'googleflightsFlight', 'meiyaApiFlight', 'fare2goApiFlight', 'biquApiRoundFlight', 'travelzenFlight',
               'pkfareFlight', 'igolaFlight', '51bookFlight', 'fliggyFlight', 'ctriptrain', 'europerailtrain',
               'voyagestrain', 'raileuropetrain', 'eurostartrain', 'bahntrain', 'sncfentrain', 'sncffrtrain',
               'tieyourailtrain', 'refentrain', 'nationalrailtrain', 'trenitaliatrain', 'cdtrain', 'loco2train',
               'travelfusionApitrain', 'theTrainLinetrain', 'miojitrain', 'amtraktrain', 'thailandrailtrain',
               'translinktrain', 'ekikaratrain', 'viarailtrain', 'germanyrailApitrain', 'korailtrain', 'ctripCar',
               'huizucheCar', 'zuzucheCar', 'idbusbus', 'megabusbus', 'directbusBusbus', 'eurolinesbus',
               'bonellibusbus', 'greyhoundbus', 'flixbusbus', 'navitimebus', 'peramatourbus', 'pattayabusbus',
               'easybookbus', 'huangbaochebaoche', 'huantaoyouwanle']

proxy_pool = ProxyPool()


class MySession(requests.Session):
    def __init__(self, need_proxies=True, auto_update_host=False, need_cache=False, do_not_delete_cache=False,
                 **kwargs):
        self.start = time.time()
        super(MySession, self).__init__()
        headers = {
            'User-Agent': random_useragent(),
            # 'Connection': 'keep-alive',
            'Connection': 'close',
        }
        # requests.adapters.DEFAULT_RETRIES = 5
        # requests.adapters.DEFAULT_POOLSIZE = 100
        self.headers = headers
        self.verify = False
        self.auto_update_host = auto_update_host
        self.md5 = []
        self.md5_resp = {}
        self.need_cache = need_cache
        self.cache_expire_time = kwargs.get('cache_expire_time', 60 * 60 * 24 * 30)
        self.do_not_delete_cache = do_not_delete_cache

        self.p_r_o_x_y = None
        if need_proxies:
            self.change_proxies()

    def request(self, method, url,
                params=None, data=None, headers=None, cookies=None, files=None,
                auth=None, timeout=None, allow_redirects=True, proxies=None,
                hooks=None, stream=None, verify=None, cert=None, json=None):
        # 请求时对错误的信息进行修改

        # 对 url 进行修改
        l_url = list(urlparse.urlsplit(url))
        if l_url[0] == '':
            l_url[0] = 'http'
            url = urlparse.urlunsplit(l_url)
        url = url.replace('\n', '')

        return super(MySession, self).request(method, url,
                                              params, data, headers, cookies, files,
                                              auth, timeout, allow_redirects, proxies,
                                              hooks, stream, verify, cert, json)

    def send(self, request, **kwargs):
        if self.auto_update_host:
            if 'Host' not in request.headers:
                request.headers['Host'] = urlparse.urlparse(request.url).netloc

        def get_resp():
            error = None
            for i in range(4):
                try:
                    pre_resp = super(MySession, self).send(request, **kwargs)
                    pre_resp.raise_for_status()
                    return pre_resp
                except (
                        requests.exceptions.Timeout,
                        requests.exceptions.ProxyError,
                        requests.exceptions.HTTPError,
                        requests.exceptions.ConnectionError,
                        requests.exceptions.RequestException
                ) as e:
                    self.change_proxies()
                    logger.exception(msg="[request retry][retry times: {}]".format(i + 1), exc_info=e)
                    error = e
                except Exception as e:
                    self.change_proxies()
                    logger.exception(msg="[request retry][retry times: {}]".format(i + 1), exc_info=e)
                    error = e
            raise error

        if self.need_cache:
            # get cache key
            req = {}
            for k, v in request.__dict__.items():
                if k in ['method', 'url', 'params', 'data', 'auth', 'json', 'body']:
                    req[k] = v

            # get cache
            md5 = proj.my_lib.Common.RespStore.calculate_md5(req)
            self.md5.append(md5)
            if not proj.my_lib.Common.RespStore.has_cache(md5):
                resp = None
            else:
                resp = proj.my_lib.Common.RespStore.get_by_md5(md5, self.cache_expire_time)

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
                resp = get_resp()
                self.md5_resp[md5] = resp
        else:
            resp = get_resp()
        return resp

    def cache_check(self, req, resp):
        return True

    def change_proxies(self):
        self.p_r_o_x_y = proxy_pool.get_proxy(random.choice(source_list))
        proxies = {
            'http': 'socks5://' + self.p_r_o_x_y,
            'https': 'socks5://' + self.p_r_o_x_y
        }
        self.proxies = proxies

        # 更新代理使用状况
        # try:
        #     get_out_ip_async(proxies)
        # except Exception:
        #     pass

        return True

    def update_proxy(self, error_code):
        # 暂时未更新代理状态
        return
        # try:
        #     update_proxy('Platform', self.p_r_o_x_y or 'NULL', time.time() - self.start, error_code)
        # except Exception:
        #     pass

    def browser_log(self):
        logger.info(self.__dict__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if not exc_type:
            self.update_proxy(0)
        elif exc_type in (SSLError, ProxyError):
            self.browser_log()
            self.update_proxy(22)
            raise ServiceStandardError(22, "代理异常 from Browser [proxy: {}]".format(self.p_r_o_x_y),
                                       wrapped_exception=exc_type)
        elif exc_type in (ConnectionError, ConnectTimeout):
            self.browser_log()
            self.update_proxy(23)
            raise ServiceStandardError(23, "代理被禁 from Browser [proxy: {}]".format(self.p_r_o_x_y),
                                       wrapped_exception=exc_type)

        if self.need_cache:
            # store page check
            if exc_type is None:
                # save any not stored cache
                for k, v in self.md5_resp.items():
                    if not proj.my_lib.Common.RespStore.has_cache(k):
                        logger.info('[保存缓存][md5: {}]'.format(k))
                        proj.my_lib.Common.RespStore.put_by_md5(k, v)
            else:
                # store debug page
                for k, v in self.md5_resp.items():
                    debug_key = "debug_{}".format(k)
                    logger.info('[保存 debug 缓存][md5: {}]'.format(debug_key))
                    if not proj.my_lib.Common.RespStore.has_cache(debug_key):
                        proj.my_lib.Common.RespStore.put_by_md5(debug_key, v)

                # don't store page or delete the page
                if not self.do_not_delete_cache:
                    for each_md5 in self.md5:
                        if proj.my_lib.Common.RespStore.has_cache(each_md5):
                            logger.info('[删除缓存][md5: {}]'.format(each_md5))
                            proj.my_lib.Common.RespStore.delete_cache(each_md5)
                else:
                    for each_md5 in self.md5:
                        logger.info('[出现异常不清楚并不清除缓存][md5: {}]'.format(each_md5))


if __name__ == '__main__':
    # with MySession() as session:
    #     page = session.get('http://www.baidu.com')
    #     print page.text

    # with MySession() as session:
    #     page = session.get(
    #         'http://www.tripadvisor.cn/ShowUrl?&excludeFromVS=false&odc=BusinessListingsUrl&d=10006331&url=0')
    #     print page.url

    # with MySession(need_proxies=False) as session:
    #     # session.headers.update({
    #     #     'Host': 'www.tripadvisor.cn'
    #     # })
    #     page = session.get(
    #         'http://bbs.qyer.com/thread-1384644-1.html')
    #     print(page.url)
    #     print(page.text)
    # raise Exception()
    print(simple_get_socks_proxy())
