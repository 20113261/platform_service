#!/usr/bin/env python
# encoding: utf-8
import requests, re
import pymongo
import urllib, pymysql
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.NetworkUtils import google_get_map_info
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Task import Task

client = pymongo.MongoClient(host='10.10.213.148')
collections = client['base_data']['station_new']


class EuropeStationSDK(BaseSDK):
    def _execute(self, **kwargs):
        city_name = self.task.kwargs['city_name']
        city_code = self.task.kwargs['city_code']
        country_code = self.task.kwargs['country_code']

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '652',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': 'partition=REInc; key=8780929146871554943; RACSESSION=rachugr51ws1; JSESSIONID=1683475BCE9E12382BF194109FEF8EA2',
            'Host': 'webservicesx.euronet.vsct.fr'
        }
        data = 'action=Native&return_url_3dpayment=http%3A%2F%2F10.101.174.163%3A52514%2Fwsclient%2Fjsp%2Foutput.jsp&partition=REInc&xmldata=%3C%3Fxml+version%3D%221.0%22%3F%3E%0A%3Crequest+serviceName%3D%22StationCache%22%3E%0A%3Ckey%3E8780929146871554943%3C%2Fkey%3E%0A%3Clocale%3Een_US%3C%2Flocale%3E%0A%3Cstyle%3E%3C%2Fstyle%3E%0A%3CtravelAgency%3E%0A++%3CagencyType%3E%3C%2FagencyType%3E%0A++%3CagencyId%3E%3C%2FagencyId%3E%0A%3C%2FtravelAgency%3E%0A%3CcityCode%3E' + city_code + '%3C%2FcityCode%3E%0A%3CcacheTimestamp%3E%3C%2FcacheTimestamp%3E%0A%3C%2Frequest%3E&key=8780929146871554943&agencyType=&agencyId=&key=https%3A%2F%2Fwebservicesx.euronet.vsct.fr%2FV10%2Fwsclient'
        url = 'https://webservicesx.euronet.vsct.fr/V10/wsclient/xml/results'

        with MySession(need_proxies=True, need_cache=True) as session:
            res = session.post(url, headers=headers, data=data, timeout=240)
            url1 = 'https://webservicesx.euronet.vsct.fr/V10/wsclient/cache' + res.content
            res1 = session.get(url1, headers=headers, verify=False, timeout=240)

            rule = '''<station><name>(.*?)</name><code>(.*?)</code><todCollectionAvailable>(.*?)</todCollectionAvailable></station>'''
            res2 = re.findall(rule, res1.content)

        for sta in res2:
            station_name = sta[0]
            station_code = sta[1]
            google_map_info = google_get_map_info('{},{},{}'.format(country_code, city_name, station_name))
            try:
                collections.save({
                    'city_code': city_code,
                    'city_name': city_name,
                    'country_code': country_code,
                    'station_name': station_name,
                    'station_code': station_code,
                    'map_info': google_map_info
                })
            except Exception:
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR)

        self.task.error_code = 0
        return 'OK'
