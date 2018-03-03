#!/usr/bin/env python
# -*- coding:utf-8 -*-
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Utils import retry
from proj.my_lib.Common.Task import Task
from lxml import html
import urllib
import pytz
import datetime
import json
import sys
import pymysql
import hashlib
import re
import requests
from Common.MiojiSimilarCityDict_new import MiojiSimilarCityDict as new_MiojiSimilarCityDict
from Common.MiojiSimilarCityDict import MiojiSimilarCityDict
from Common.MiojiSimilarCountryDict import MiojiSimilarCountryDict
source_interface = {
    'hotels': 'https://lookup.hotels.com/1/suggest/v1.7/json?' + \
        'locale=zh_CN&boostConfig=config-boost-champion&excludeLpa=false&callback=srs&query={0}',

    'agoda': 'https://www.agoda.com/Search/Search/GetUnifiedSuggestResult/3/8/1/0/zh-cn?' \
        'guid=9c6be1f0-e830-41e6-989c-0161a7b486c3&searchText={0}&origin=CN&cid=-1&pageTypeId=1&' \
        'logtime={1}&logTypeId=1&qs=%7Cexplist%3D%26expuser%3D%7C&isHotelLandSearch=true',

    'elong': 'http://ihotel.elong.com/ajax/sugInfo?datatype=Region&keyword={0}',
    'booking': 'http://www.booking.com/autocomplete_2?' + \
        'v=1&lang=zh-cn&sid=856b717ff095a5294d897d227d9e7ef4&aid=376390&pid=9bb13ce9aca502d0&stype=1&src=index&eb=4&e_obj_labels=1&at=1&e_tclm=1&e_smmd=2&e_ms=1&e_msm=1&e_themes_msm_1=1&add_themes=1&themes_match_start=1&include_synonyms=1&sort_nr_destinations=1&gpf=1&term={0}',
    'expedia': 'https://suggest.expedia.com/api/v4/typeahead/{0}?client=Homepage&siteid=18&guid=cf20f4e625d7418399d0954735abcb77&lob=PACKAGES&locale=zh_CN&expuserid=-1&regiontype=95&ab=&dest=true&maxresults=9&features=ta_hierarchy&format=jsonp&device=Desktop&browser=Chrome&_=1503623716328',
    'ctrip': 'http://hotels.ctrip.com/international/Tool/cityFilter.ashx?charset=gb2312&flagship=1&keyword={0}',
}
config = {
        'host': '10.10.230.206',
        'user': 'mioji_admin',
        'password': 'mioji1109',
        'db': '',
        'charset': 'utf8'
}
base_data_config = {
    'host': '10.10.69.170',
    'user': 'reader',
    'password': 'miaoji1109',
    'db': 'base_data',
    'charset': 'utf8'
}
def get_elong_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    suggest = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    key_city_id = city_id
    key_country_id = country_id
    key_country_name = get_country_name(key_country_id)
    try:
        citys = suggest['data'].get('city',[])
        for city in citys:
            source = 'elong'
            city_name = city['name_cn']
            country_name = city['region_info']['country_name_cn']
            region_name = city['region_info']['province_name_cn']
            if city_name[:len(keyword)] != keyword and len(city_name) >= len(keyword) and country_name != key_country_name:
                continue
            else:
                city_id = key_city_id
                country_id = key_country_id
            if not region_name:
                region_name = 'NULL'
            sid = str(city['id'])
            md5 = hashlib.md5()
            md5.update(sid)
            sid_md5 = md5.hexdigest()
            local_time = str(datetime.datetime.now())[:10]
            label_batch = ''.join([local_time, 'a'])
            str_suggest = json.dumps(city)
            if city_name[:len(keyword)] == keyword and len(city_name) >= len(keyword) and country_name == key_country_name:
                save_result.append([source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,region_name,country_name,'NULL',label_batch])
        config['db'] = database_name
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, save_result)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    except Exception as e:
        raise e
    return len(save_result)
def get_ctrip_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    suggest = suggest.decode('gbk')
    suggest = suggest.replace('cQuery.jsonpResponse=','').replace(';','')
    suggest = json.loads(suggest)
    infos = suggest.get('data').strip('@')
    info_list = infos.split('@')
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    key_city_id = city_id
    key_country_id = country_id
    key_country_name = get_country_name(country_id)
    for info in info_list:
        if 'city' in info:
            detail_infos = info.split('|')[1:-1]
            source = 'ctrip'
            country = detail_infos[0].split('，')[-1]
            city = detail_infos[0].split('，')[0]
            if city != keyword and country != key_country_name:
                continue
            else:
                city_id = key_city_id
                country_id = key_country_id
            sid = ''.join([detail_infos[3],detail_infos[4]])
            md5 = hashlib.md5()
            md5.update(sid)
            sid_md5 = md5.hexdigest()
            local_time = str(datetime.datetime.now())[:10]
            label_batch = ''.join([local_time,'a'])
            str_suggest = info
            if city == keyword and country == key_country_name:
                save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city,'NULL',country,'NULL',label_batch))
    config['db'] = database_name
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.executemany(sql,save_result)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return len(save_result)
def get_expedia_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    pattern = re.search(r'(?<=\()(.*)(?=\))', suggest)
    suggest = pattern.group(1)
    suggest = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch,others_info) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    citys = suggest['sr']
    key_city_id = city_id
    key_country_id = country_id
    key_country_name = get_country_name(country_id)
    for city in citys:
        city_type = city['type']
        if city_type == 'CITY' or city_type == 'MULTICITY':
            others_info = {}
            lat = city['coordinates']['lat']
            long = city['coordinates']['long']
            suggest_map_info = ','.join([long, lat])
            country_name = city['hierarchyInfo']['country']['name']
            city_name = city['regionNames']['shortName']
            if city_name[:len(keyword)] != keyword and len(city_name) >= len(keyword) and country_name != key_country_name:
                continue
            else:
                country_id,city_id = get_city_country_id(city_name,country_name,suggest_map_info)
            source = 'expedia'
            sid = city['gaiaId']

            others_info['map_info'] = suggest_map_info
            others_info = json.dumps(others_info)
            md5 = hashlib.md5()
            md5.update(sid)
            sid_md5 = md5.hexdigest()
            str_suggest = json.dumps(city)
            local_time = str(datetime.datetime.now())[:10]
            label_batch = ''.join([local_time, 'a'])
            if city_name[:len(keyword)] == keyword and country_name == key_country_name:
                save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,'NULL',country_name,'NULL',label_batch,others_info))
    config['db'] = database_name
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.executemany(sql, save_result)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        conn.close()
    return len(save_result)
def get_booking_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    suggest = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch,others_info) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    citys = suggest['city']
    key_city_id = city_id
    key_country_id = country_id
    key_country_name = get_country_name(country_id)
    try:
        for city in citys:
            city_type = city['dest_type']
            if city_type == 'city':
                source = 'booking'
                sid = city['dest_id']
                md5 = hashlib.md5()
                md5.update(sid)
                sid_md5 = md5.hexdigest()
                lat = str(city['latitude'])
                long = str(city['longitude'])
                others_info = {}
                map_info = ','.join([long, lat])
                labels = city['labels']
                for label in labels:
                    if label['type'] == 'city':
                        city_name = label['text']
                    elif label['type'] == 'region':
                        region_name = label['text']
                    elif label['type'] == 'country':
                        country_name = label['text']
                if city_name not in keyword and country_name != key_country_name:
                    continue
                else:
                    country_id,city_id = get_city_country_id(city_name,country_name,map_info)
                others_info['map_info'] = map_info
                others_info = json.dumps(others_info)
                local_time = str(datetime.datetime.now())[:10]
                label_batch = ''.join([local_time, 'a'])
                str_suggest = json.dumps(city)
                if city_name in keyword and country_name == key_country_name:
                    save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,region_name,country_name,'NULL',label_batch,others_info))
    except Exception as e:
        raise e
    config['db'] = database_name
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.executemany(sql, save_result)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return len(save_result)
def get_hotels_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    pattern = re.search(r'(?<=srs\()(.*)(?=\);)', suggest)
    suggest = pattern.group(1)
    suggest = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch,others_info) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    key_country_id = country_id
    key_city_id = city_id
    key_country_name = get_country_name(country_id)
    try:
        suggestions = suggest['suggestions']
        for suggestion in suggestions:
            citys = suggestion['entities']
            for city in citys:
                city_type = city['type']
                if city_type != 'CITY':
                    continue
                source = 'hotels'
                country_name = city['caption'].split(',')[-1]
                country_name = re.search(u'[\u4e00-\u9fa5]+',country_name).group()
                city_name = city['name']
                others_info = {}
                lat = str(city['latitude'])
                long = str(city['longitude'])
                map_info = ','.join([long, lat])
                if city_name != keyword and country_name != key_country_name:
                    continue
                else:
                    country_id,city_id = get_city_country_id(city_name,country_name,map_info)
                sid = city['geoId']
                md5 = hashlib.md5()
                md5.update(sid)
                sid_md5 = md5.hexdigest()

                others_info['map_info'] = map_info
                others_info = json.dumps(others_info)
                local_time = str(datetime.datetime.now())[:10]
                label_batch = ''.join([local_time, 'a'])
                str_suggest = json.dumps(city)
                if city_name == keyword and country_name == key_country_name:
                    save_result.append(
                        (source, sid_md5, sid, 2, str_suggest, city_id, country_id, city_name, 'NULL', country_name, 'NULL', label_batch,others_info))
        config['db'] = database_name
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, save_result)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    except Exception as e:
        raise e
    return len(save_result)
def get_agoda_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    suggest = json.loads(suggest)
    suggestionlist = suggest['ViewModelList']
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    key_city_id = city_id
    key_country_id = country_id
    save_result = []
    key_country_name = get_country_name(country_id)
    for city_info in suggestionlist:
        city_type = city_info['PageTypeId']
        if int(city_type) == 5:
            city_name = city_info['KnowledgeGraphCityName']
            country_name = city_info['KnowledgeGraphCountryName']
            if not city_name:
                continue
            if city_name != keyword and country_name != key_country_name:
                continue
            else:
                country_id = key_country_id
                city_id = key_city_id
            source = 'agoda'
            sid = str(city_info['ObjectID'])
            md5 = hashlib.md5()
            md5.update(sid)
            sid_md5 = md5.hexdigest()
            local_time = str(datetime.datetime.now())[:10]
            label_batch = ''.join([local_time, 'a'])
            str_suggest = json.dumps(city_info)

            if city_name == keyword and country_name == key_country_name:
                save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,'NULL','NULL','NULL',label_batch))
    config['db'] = database_name
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.executemany(sql, save_result)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return len(save_result)

def get_city_country_id(city_name,country_name,map_info=None):
    mioji_country = MiojiSimilarCountryDict()
    mioji_city = MiojiSimilarCityDict()
    new_mioji_city = new_MiojiSimilarCityDict()
    country_id = mioji_country.get_mioji_country_id(country_name)
    if map_info:
        city_objects = new_mioji_city.get_mioji_city_id([country_name,city_name],map_info)
        city_id = city_objects[0].cid
    else:
        city_objects = mioji_city.get_mioji_city_id([country_name,city_name])
        city_id = city_objects[0]
    return country_id,city_id

def get_country_name(country_id):
    select_country = "select name from country where mid=%s"
    conn = pymysql.connect(**base_data_config)
    cursor = conn.cursor()
    cursor.execute(select_country,(country_id,))
    country_name = cursor.fetchone()[0]
    return country_name

class AllHotelSourceSDK(BaseSDK):

    @retry(times=5)
    def _execute(self, **kwargs):

        with MySession(need_cache=True,need_proxies=True) as session:
            try:
                keyword = self.task.kwargs['keyword']
                source = self.task.kwargs['source']
                map_info = self.task.kwargs['map_info']
                country_id = self.task.kwargs['country_id']
                city_id = self.task.kwargs['city_id']
                database_name = self.task.kwargs['database_name']
                local_time = urllib.unquote(datetime.datetime.now(pytz.timezone(pytz.country_timezones('cn')[0])).strftime(
                    '%a %b %d %Y %H:%M:%S GMT+0800 (%Z)'))
                if source in 'agoda':
                    url = source_interface[source].format(keyword,local_time)
                    header = {
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'accept': 'application/json, text/javascript, */*; q=0.01',
                        'referer': 'https://www.agoda.com/zh-cn/',
                        'authority': 'www.agoda.com',
                        'x-requested-with': 'XMLHttpRequest'
                    }
                    response = session.get(url=url,headers=header)
                    get_suggest = getattr(sys.modules[__name__], 'get_{0}_suggest'.format(source))
                else:
                    url = source_interface[source].format(keyword)
                    response = session.get(url=url,)
                    get_suggest = getattr(sys.modules[__name__],'get_{0}_suggest'.format(source))

                count = get_suggest(response.content,map_info,country_id,city_id,database_name,keyword)
            except Exception as e:
                print(e)
                raise ServiceStandardError(ServiceStandardError.REQ_ERROR,wrapped_exception=e)
            if count >= 0:
                self.task.error_code = 0
        return count

if __name__ == "__main__":
    args = {
        'keyword': '圣卡洛斯市',
        'source': 'expedia',
        'map_info': '0.0',
        'country_id':'107',
        'city_id': '10002',
        'database_name': 'add_city_673'
    }
    task = Task(_worker='', _task_id='demo', _source='hotels', _type='supplement_field',
                _task_name='all_hotels_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='supplement_field',
                _routine_key='supplement_field', list_task_token='test', task_type=0, collection='')
    normal = AllHotelSourceSDK(task)
    normal.execute()