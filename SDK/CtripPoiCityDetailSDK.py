#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
@author: feng
@date: 18-02-26
'''
import pymongo
import pymongo.errors
import requests.exceptions
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Task import Task
import json
from lxml import html
import re

logger = get_logger('ctripPoi_suggest')

client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
db = client['SuggestName']

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding":"gzip, deflate",
    "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8",
    "Connection":"keep-alive",
    "Host":"you.ctrip.com",
    "Upgrade-Insecure-Requests":"1",
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"
}
search_url = 'http://you.ctrip.com/map/{}.html'

class CtripPoiDetailSDK(BaseSDK):

    def _execute(self, **kwargs):

        with MySession(need_proxies=True, need_cache=True) as session:
            keyword = self.task.kwargs['keyword']
            suggest = {}
            try:
                response = requests.get(
                    url=search_url.format(keyword),
                    headers=headers
                )

                res = response.content
                root = html.fromstring(res)
                dests = root.xpath("//div[@class='breadbar_v1 cf']/ul/li")
                dest = ''
                for de in dests[2:-1]:
                    if dest != '':
                        dest += '|'
                    dest += de.xpath("a/text()")[0]
                print dest
                tags = root.xpath("//ul[@class='map_tab cf']/li")
                tag = {}
                for ta in tags:
                    t = ta.xpath('a/span/text()')[0]
                    tt = ta.xpath('a/text()')[-1].strip()
                    tag[t] = tt
                print tag
                map_info = ''
                map_info = re.findall('centerGeo: ({.+})', res)[0].replace('\'', '\"')
                print map_info

                db = client['SuggestName']
                db.CtripPoiSDK_detail.save({
                    'dest':dest,
                    'tag_info':tag,
                    'map_info':map_info
                })
                self.task.error_code = 0
                return 'OK'
            except requests.exceptions.RequestException as e:
                raise ServiceStandardError(ServiceStandardError.PROXY_INVALID, wrapped_exception=e)
            except pymongo.errors.PyMongoError as e:
                raise ServiceStandardError(ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)
            except Exception as e:
                raise ServiceStandardError(ServiceStandardError.UNKNOWN_ERROR, wrapped_exception=e)


if __name__ == "__main__":
    all = []
    for ce in db.CtripPoiSDK.find({}):
        try:
            s = ce['suggest']['List']
        except:
            continue
        for sug in ce['suggest']['List']:

            args = {
                'name':sug['Name'],
                'dest_name':sug['DestName'],
                'keyword': sug['Url'].split('.')[0].split('/')[-1]
            }
            all.append(args)

    for args in all:
        task = Task(_worker='', _task_id='demo', _source='ctirppoi', _type='poi_list', _task_name='ctrip_poi_suggest',
                    _used_times=0, max_retry_times=6,
                    kwargs=args, _queue='poi_list',
                    _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
        normal = CtripPoiDetailSDK(task)

        normal.execute()

