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
from collections import defaultdict
from proj.my_lib.Common.Utils import retry
from proj.my_lib.logger import get_logger

logger = get_logger("proxy_pool")

PROXY_NUM_EACH_TIMES = 100

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
    msg = {
        "req": [
            {
                "source": source,
                "type": "platform",
                "num": PROXY_NUM_EACH_TIMES,
                "ip_type": "",
            }
        ]
    }

    qid = time.time()
    ptid = "platform"

    try:
        get_info = '/?type=px001&qid={0}&query={1}&ptid={2}&tid=tid&ccy=AUD'.format(qid, json.dumps(msg), ptid)
        logger.info("get proxy info :http://10.10.189.85:48200{0}".format(get_info))
        p = requests.get("http://10.10.32.22:48200" + get_info).content
        time_end = time.time() - time_st
        logger.info("获取到代理，代理信息{0},获取代理耗时{1}".format(p, time_end))
        logger.info(p)
        ps = json.loads(p)['resp'][0]['ips']
        return ps
    except Exception:
        raise Exception("Error Proxy")


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
