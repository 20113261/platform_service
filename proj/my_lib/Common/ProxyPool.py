#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/28 下午4:10
# @Author  : Hou Rong
# @Site    : 
# @File    : ProxyPool.py
# @Software: PyCharm
import time
import requests
import json
import random
from collections import defaultdict
from proj.my_lib.Common.Utils import retry
from proj.my_lib.logger import get_logger

logger = get_logger("proxy_pool")

PROXY_NUM_RANGE = (70, 150)

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


@retry(times=3)
def simple_get_socks_proxy(source):
    time_st = time.time()
    logger.info("开始获取代理")

    proxy_num = random.randint(*PROXY_NUM_RANGE)
    logger.info("[get proxy][source: {}][num: {}]".format(source, proxy_num))
    msg = {
        "req": [
            {
                "source": source,
                "type": "platform",
                "num": proxy_num,
                "ip_type": "",
            }
        ]
    }

    qid = time.time()
    ptid = "platform"

    try:
        get_info = '/?type=px001&qid={0}&query={1}&ptid={2}&tid=tid&ccy=AUD'.format(qid, json.dumps(msg), ptid)
        logger.info("get proxy info :http://10.10.135.140:92{0}".format(get_info))
        p = requests.get("http://10.10.135.140:92" + get_info).content
        time_end = time.time() - time_st
        logger.info("获取到代理，代理信息{0},获取代理耗时{1}".format(p, time_end))
        logger.info(p)
        ps = json.loads(p)['resp'][0]['ips']
        return ps
    except Exception as exc:
        logger.exception(msg="[Error Proxy]", exc_info=exc)
        return [{"external_ip": "14.191.122.185", "inner_ip": "10.10.217.150:38984"},
                {"external_ip": "113.184.234.249", "inner_ip": "10.19.50.223:38013"},
                {"external_ip": "27.64.54.134", "inner_ip": "10.10.233.246:33534"},
                {"external_ip": "217.55.144.197", "inner_ip": "10.10.233.246:32902"},
                {"external_ip": "5.175.78.86", "inner_ip": "10.10.233.246:39286"},
                {"external_ip": "113.161.76.84", "inner_ip": "10.10.233.246:36262"},
                {"external_ip": "113.171.168.58", "inner_ip": "10.19.50.223:36850"},
                {"external_ip": "27.64.153.108", "inner_ip": "10.10.233.246:30764"},
                {"external_ip": "85.117.129.164", "inner_ip": "10.19.50.223:33941"},
                {"external_ip": "113.180.38.30", "inner_ip": "10.10.217.150:34759"},
                {"external_ip": "112.197.33.210", "inner_ip": "10.10.233.246:32573"},
                {"external_ip": "78.72.1.222", "inner_ip": "10.19.50.223:38463"},
                {"external_ip": "27.75.37.121", "inner_ip": "10.10.217.150:35100"},
                {"external_ip": "85.98.6.46", "inner_ip": "10.19.50.223:33179"},
                {"external_ip": "88.233.106.7", "inner_ip": "10.19.50.223:34195"},
                {"external_ip": "203.205.52.151", "inner_ip": "10.19.50.223:37500"},
                {"external_ip": "118.70.170.118", "inner_ip": "10.19.50.223:34543"},
                {"external_ip": "1.54.213.153", "inner_ip": "10.10.233.246:32697"},
                {"external_ip": "128.199.105.4", "inner_ip": "10.19.50.223:39046"},
                {"external_ip": "118.71.190.33", "inner_ip": "10.10.233.246:31264"},
                {"external_ip": "14.165.247.80", "inner_ip": "10.10.233.246:34237"},
                {"external_ip": "109.252.99.188", "inner_ip": "10.10.233.246:34785"},
                {"external_ip": "70.139.118.87", "inner_ip": "10.10.233.246:38224"},
                {"external_ip": "113.189.100.207", "inner_ip": "10.10.233.246:36923"},
                {"external_ip": "46.242.12.43", "inner_ip": "10.19.50.223:38465"},
                {"external_ip": "42.118.136.114", "inner_ip": "10.19.50.223:33706"},
                {"external_ip": "123.25.43.224", "inner_ip": "10.10.233.246:33456"},
                {"external_ip": "123.27.121.187", "inner_ip": "10.10.217.150:35004"},
                {"external_ip": "42.116.83.135", "inner_ip": "10.10.233.246:31226"},
                {"external_ip": "1.55.176.111", "inner_ip": "10.19.50.223:37322"},
                {"external_ip": "183.91.7.240", "inner_ip": "10.10.217.150:37244"},
                {"external_ip": "94.60.226.252", "inner_ip": "10.10.233.246:33318"},
                {"external_ip": "14.172.161.122", "inner_ip": "10.10.233.246:30247"},
                {"external_ip": "113.181.210.93", "inner_ip": "10.10.217.150:35703"},
                {"external_ip": "123.28.37.32", "inner_ip": "10.10.217.150:34977"},
                {"external_ip": "123.18.213.228", "inner_ip": "10.10.233.246:37975"},
                {"external_ip": "1.52.33.152", "inner_ip": "10.10.233.246:38276"},
                {"external_ip": "14.183.50.16", "inner_ip": "10.10.217.150:33113"},
                {"external_ip": "37.132.27.26", "inner_ip": "10.10.233.246:38083"},
                {"external_ip": "110.78.183.70", "inner_ip": "10.10.217.150:37847"},
                {"external_ip": "171.238.42.88", "inner_ip": "10.19.50.223:37706"},
                {"external_ip": "27.64.91.165", "inner_ip": "10.10.217.150:36843"},
                {"external_ip": "1.53.223.151", "inner_ip": "10.10.217.150:35675"},
                {"external_ip": "1.55.177.69", "inner_ip": "10.19.50.223:33127"},
                {"external_ip": "42.113.162.171", "inner_ip": "10.19.50.223:37672"},
                {"external_ip": "171.227.170.164", "inner_ip": "10.19.50.223:30909"},
                {"external_ip": "171.253.90.131", "inner_ip": "10.10.217.150:33234"},
                {"external_ip": "42.117.107.233", "inner_ip": "10.10.233.246:33216"},
                {"external_ip": "42.114.32.213", "inner_ip": "10.19.50.223:38156"},
                {"external_ip": "116.106.79.143", "inner_ip": "10.19.50.223:35345"},
                {"external_ip": "183.80.138.160", "inner_ip": "10.19.50.223:38523"},
                {"external_ip": "113.190.102.29", "inner_ip": "10.10.233.246:38040"},
                {"external_ip": "118.69.162.161", "inner_ip": "10.10.233.246:39118"},
                {"external_ip": "117.3.212.51", "inner_ip": "10.19.50.223:36193"},
                {"external_ip": "118.68.242.140", "inner_ip": "10.10.233.246:38852"},
                {"external_ip": "14.189.134.38", "inner_ip": "10.19.50.223:38222"},
                {"external_ip": "42.114.13.168", "inner_ip": "10.19.50.223:35366"},
                {"external_ip": "1.52.53.98", "inner_ip": "10.10.217.150:38971"},
                {"external_ip": "14.189.123.56", "inner_ip": "10.10.233.246:36821"},
                {"external_ip": "42.113.164.25", "inner_ip": "10.10.217.150:33547"},
                {"external_ip": "1.52.35.210", "inner_ip": "10.10.233.246:31492"},
                {"external_ip": "42.114.18.199", "inner_ip": "10.10.217.150:39607"},
                {"external_ip": "113.183.200.153", "inner_ip": "10.10.217.150:30886"},
                {"external_ip": "58.186.145.9", "inner_ip": "10.10.233.246:37359"},
                {"external_ip": "41.13.94.146", "inner_ip": "10.10.217.150:37214"},
                {"external_ip": "113.174.82.245", "inner_ip": "10.10.217.150:34356"},
                {"external_ip": "58.186.28.230", "inner_ip": "10.19.50.223:31966"},
                {"external_ip": "116.101.90.37", "inner_ip": "10.10.217.150:38878"},
                {"external_ip": "46.152.56.199", "inner_ip": "10.10.233.246:33458"},
                {"external_ip": "113.162.50.180", "inner_ip": "10.10.217.150:32553"},
                {"external_ip": "1.54.113.0", "inner_ip": "10.10.217.150:31343"},
                {"external_ip": "116.105.123.238", "inner_ip": "10.10.217.150:37046"},
                {"external_ip": "177.209.112.170", "inner_ip": "10.10.217.150:33395"},
                {"external_ip": "118.70.121.95", "inner_ip": "10.19.50.223:38675"}]
        # raise Exception("Error Proxy")


class ProxyPool(object):
    def __init__(self):
        self.pool = defaultdict(list)

    def __generate_proxy(self, source):
        proxy_list = simple_get_socks_proxy(source)
        self.pool[source].extend(proxy_list)

    def get_proxy(self, source):
        if len(self.pool[source]) < 10:
            self.__generate_proxy(source)
        proxy = self.pool[source].pop()
        logger.info("[get proxy][source: {}][info: {}]".format(source, proxy))
        return proxy['inner_ip']
