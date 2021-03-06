#!/usr/bin/env python
# -*- coding:utf-8 -*-
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Utils import retry
from proj.my_lib.Common.Task import Task
import execjs
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
import time
# from Common.MiojiSimilarCityDict_new import MiojiSimilarCityDict as new_MiojiSimilarCityDict
# from Common.MiojiSimilarCityDict import MiojiSimilarCityDict
# from Common.MiojiSimilarCountryDict import MiojiSimilarCountryDict
# from Common.CityMapClient import run
# import memory_profiler
# import psutil
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
    #'ctrip': 'http://hotels.ctrip.com/international/Tool/cityFilter.ashx?charset=gb2312&flagship=1&keyword={0}',
    'ctrip': 'http://hotels.ctrip.com/international/Tool/cityFilter.ashx?charset=gb2312&keyword={0}&flagship=1',
    'daodao': 'https://www.tripadvisor.cn/TypeAheadJson',
    'qyer': 'http://www.qyer.com/qcross/home/ajax?action=search&keyword={0}'
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

# mioji_country = MiojiSimilarCountryDict()
# country_dict = mioji_country.dict
def get_elong_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    config['db'] = database_name
    suggest = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    config['db'] = database_name
    key_country_id = country_id
    key_country_name = get_country_name(key_country_id)
    try:
        citys = suggest['data'].get('city',[])
        for city in citys:
            source = 'elong'
            city_name = city['name_cn']
            country_name = city['region_info']['country_name_cn']
            region_name = city['region_info']['province_name_cn']
            if country_name in country_dict:
                country_id = country_dict[country_name]
            city_id = run(country_name,city_name,province=region_name)
            if not region_name:
                region_name = 'NULL'
            sid = str(city['id'])
            md5 = hashlib.md5()
            md5.update(sid)
            sid_md5 = md5.hexdigest()
            local_time = str(datetime.datetime.now())[:10]
            label_batch = ''.join([local_time, 'a'])
            str_suggest = json.dumps(city)
            keyword = keyword.decode('utf-8')
            if city_name[:len(keyword)] == keyword and country_name == key_country_name and city_id != 'NULL':
                save_result.append([source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,region_name,country_name,'NULL',label_batch])

        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        if len(save_result) > 1:
            return 0
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
    config['db'] = database_name
    suggest = suggest.decode('gbk')
    suggest = suggest.replace('cQuery.jsonpResponse=','').replace(';','')
    save_result = []
    try:
        suggest = json.loads(suggest)
        infos = suggest.get('data').strip('@')
        info_list = infos.split('@')
    except Exception as e:
        return len(save_result)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    key_country_name = get_country_name(country_id)
    for info in info_list:
        if 'city' in info:
            detail_infos = info.split('|')[1:-1]
            source = 'ctrip'
            country = detail_infos[0].split('，')[-1]
            city = detail_infos[0].split('，')[0]
            if country in country_dict:
                country_id = country_dict[country]
            city_id = run(country,city)

            sid = ''.join([detail_infos[3],detail_infos[4]])
            md5 = hashlib.md5()
            md5.update(sid)
            sid_md5 = md5.hexdigest()
            local_time = str(datetime.datetime.now())[:10]
            label_batch = ''.join([local_time,'a'])
            str_suggest = info
            keyword = keyword.decode('utf-8')
            if city[:len(keyword)] == keyword and country == key_country_name and city_id != 'NULL':
                save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city,'NULL',country,'NULL',label_batch))
    config['db'] = database_name
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    if len(save_result) > 1:
        return 0
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
    config['db'] = database_name
    pattern = re.search(r'(?<=\()(.*)(?=\))', suggest)
    suggest = pattern.group(1)
    suggest = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch,others_info) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    try:
        citys = suggest['sr']
    except Exception as e:
        return save_result
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
            if country_name in country_dict:
                country_id = country_dict[country_name]
            city_id = run(country_name,city_name,suggest_map_info)
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
            keyword = keyword.decode('utf-8')
            if city_name[:len(keyword)] == keyword and country_name == key_country_name and city_id != 'NULL':
                save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,'NULL',country_name,'NULL',label_batch,others_info))

    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    if len(save_result) > 1:
        return 0
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
    config['db'] = database_name
    suggest = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch,others_info) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    citys = suggest['city']
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
                if country_name in country_dict:
                    country_id = country_dict[country_name]
                city_id = run(country_name,city_name,map_info,region_name)

                others_info['map_info'] = map_info
                others_info = json.dumps(others_info)
                local_time = str(datetime.datetime.now())[:10]
                label_batch = ''.join([local_time, 'a'])
                str_suggest = json.dumps(city)
                keyword = keyword.decode('utf-8')
                if city_name[:len(keyword)] == keyword and country_name == key_country_name and city_id != 'NULL':
                    save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,region_name,country_name,'NULL',label_batch,others_info))
    except Exception as e:
        raise e
    if len(save_result) > 1:
        return 0
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
    config['db'] = database_name
    pattern = re.search(r'(?<=srs\()(.*)(?=\);)', suggest)
    suggest = pattern.group(1)
    suggest = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch,others_info) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
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
                if country_name in country_dict:
                    country_id = country_dict[country_name]
                city_id = run(country_name,city_name,map_info)

                sid = city['geoId']
                md5 = hashlib.md5()
                md5.update(sid)
                sid_md5 = md5.hexdigest()
                others_info['map_info'] = map_info
                others_info = json.dumps(others_info)
                local_time = str(datetime.datetime.now())[:10]
                label_batch = ''.join([local_time, 'a'])
                str_suggest = json.dumps(city)
                keyword = keyword.decode('utf-8')
                if city_name[:len(keyword)] == keyword and country_name == key_country_name and city_id != 'NULL':
                    save_result.append(
                        (source, sid_md5, sid, 2, str_suggest, city_id,country_id, city_name, 'NULL', country_name, 'NULL', label_batch,others_info))
        if len(save_result) > 1:
            return 0
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
    save_result = []
    try:
        suggestionlist = suggest['ViewModelList']
    except Exception as e:
        return len(save_result)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    config['db'] = database_name
    key_country_name = get_country_name(country_id)
    for city_info in suggestionlist:
        city_type = city_info['PageTypeId']
        if int(city_type) == 5:
            try:
                city_name = city_info['Name']
                country_name = city_info['ResultText'].split(',')[-1].strip()
                if not city_name:
                    continue
                if country_name in country_dict:
                    country_id = country_dict[country_name]
                city_id = run(country_name,city_name)

                source = 'agoda'
                sid = str(city_info['ObjectId'])
                md5 = hashlib.md5()
                md5.update(sid)
                sid_md5 = md5.hexdigest()
                local_time = str(datetime.datetime.now())[:10]
                label_batch = ''.join([local_time, 'a'])
                str_suggest = json.dumps(city_info)
                keyword = keyword.decode('utf-8')
                if city_name[:len(keyword)] == keyword and country_name == key_country_name and city_id != 'NULL':
                    save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,'NULL','NULL','NULL',label_batch))
            except Exception as e:
                print e
    config['db'] = database_name
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    if len(save_result) > 1:
        return 0
    try:
        cursor.executemany(sql, save_result)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return len(save_result)

def get_daodao_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    config['db'] = database_name
    suggest_infos = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch,others_info) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    key_country_name = get_country_name(country_id)
    for suggest_info in suggest_infos:
        city_type = suggest_info['type']
        others_info = {}
        if city_type == 'GEO':

            source = 'daodao'
            name = suggest_info['name']
            city_name = name.split(',')[0].strip()
            country_name = name.split(',')[-1].strip()
            try:
                lat,long = suggest_info['coords'].split(',')
            except:
                continue
            map_info = ','.join([long,lat])
            if country_name in country_dict:
                country_id = country_dict[country_name]
            city_id = run(country_name,city_name,map_info)
            others_info['map_info'] = map_info
            others_info = json.dumps(others_info)
            sid = str(suggest_info['value'])
            md5 = hashlib.md5()
            md5.update(sid)
            sid_md5 = md5.hexdigest()

            local_time = str(datetime.datetime.now())[:10]
            label_batch = ''.join([local_time, 'a'])
            str_suggest = json.dumps(suggest_info)
            keyword = keyword.decode('utf-8')

            if city_name[:len(keyword)] == keyword and country_name == key_country_name and city_id != 'NULL':
                save_result.append((source,sid_md5,sid,2,str_suggest,city_id,country_id,city_name,'NULL',country_name,'NULL',label_batch,others_info))
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    if len(save_result) > 1:
        return 0
    try:
        cursor.executemany(sql, save_result)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return len(save_result)

def get_qyer_suggest(suggest,map_info,country_id,city_id,database_name,keyword):
    config['db'] = database_name
    suggests = json.loads(suggest)
    sql = "insert ignore into ota_location(source,sid_md5,sid,suggest_type,suggest,city_id,country_id,s_city,s_region,s_country,s_extra,label_batch) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    save_result = []
    try:
        suggest_infos = suggests['data']['list']
    except Exception as e:
        return save_result
    for suggest_info in suggest_infos:
        city_type = suggest_info['type_name']
        source = 'qyer'
        if city_type == 'city':
            city_name = suggest_info['cn_name'].replace('<span class="cGreen">','').replace('</span>','')
            if city_name == keyword:
                country_name = get_country_name(country_id)
                if country_name in country_dict:
                    country_id = country_dict[country_name]
                city_id = run(country_name,city_name)

                url = suggest_info['url']
                if str(url).endswith('/'):
                    sid = url.split('/')[-2]
                else:
                    sid = url.split('/')[-1]
                md5 = hashlib.md5()
                md5.update(sid)
                sid_md5 = md5.hexdigest()
                str_suggest = ''.join(['http:',url])
                local_time = str(datetime.datetime.now())[:10]
                label_batch = ''.join([local_time, 'a'])
                save_result.append((source,sid_md5,sid,1,str_suggest,city_id,country_id,city_name,'NULL',country_name,'NULL',label_batch))
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


def get_city_country_id(city_name,country_name,map_info=None,config=None):

    mioji_city = MiojiSimilarCityDict(config)
    new_mioji_city = new_MiojiSimilarCityDict(config)
    country_id = mioji_country.get_mioji_country_id(country_name)
    if not country_id:
        country_id = 'NULL'
    if map_info:
        city_objects = new_mioji_city.get_mioji_city_id([country_name,city_name],map_info,config)
        if city_objects:
            city_id = city_objects[0].cid
        else:
            city_id = 'NULL'
    else:
        city_objects = mioji_city.get_mioji_city_id([country_name,city_name],config)
        if city_objects and len(city_objects) == 1:
            city_id = city_objects.pop()
        else:
            city_id = 'NULL'
    return country_id,city_id

def get_country_name(country_id):
    select_country = "select name from country where mid=%s"
    conn = pymysql.connect(**base_data_config)
    cursor = conn.cursor()
    cursor.execute(select_country,(country_id,))
    country_name = cursor.fetchone()[0]
    return country_name

def get_ctrip_eleven(max_n):
    try:
        ph_runtime = execjs.get('PhantomJS')
    except Exception as e:
        raise e
    do = 'var Image = function(){}; var window = {}; window.document = {}; ' \
         'var document = window.document; ' \
         'window.navigator = ' \
         '{"appCodeName":"Mozilla", "appName":"Netscape", "language":"zh-CN", "platform":"Win"}; ' \
         'var navigator = window.navigator; window.location = {}; ' \
         'window.location.href = "http://hotels.ctrip.com/hotel/hotelid.html"; ' \
         'var location = window.location; '
    mixjs = ph_runtime.compile("""

            function generateMixed (n) {
            var chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'];
            var res = '';

            for (var i = 0; i < n; i++) {
                var id = Math.ceil(Math.random() * 51);
                res += chars[id];
            }

            return res;
        }
        """)
    call_back = mixjs.call("generateMixed", max_n)
    callback_req = "http://hotels.ctrip.com/international/Tool/cas-ocanball.aspx?callback=%s&" % (
        str(call_back))
    headers = {
        'Host': 'hotels.ctrip.com',
        'Referer': 'http://hotels.ctrip.com/international/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.360',
        'Connection': 'keep-alive',
    }
    pat = re.compile(r'new Function\(\'return "\' \+ (.+) \+ \'\";\'\)')
    pat2 = re.compile(r'new Function\(\'return "\' \+ .+ \+ \'\";\'\)')
    response = requests.get(callback_req,headers=headers,params= {'_': str(int(time.time() * 1000))})
    jscontent = response.content
    jscontent = jscontent.replace('eval(', '')[:-1]  # 加密的javaScript
    runjs = ph_runtime.eval(jscontent)
    eleven_str = pat.findall(runjs)
    need_to_replace = pat2.findall(runjs)
    replace_str = call_back + '(' + need_to_replace[0] + ')'
    js = runjs.replace(replace_str, 'return ' + eleven_str[0])
    js = do + js
    js = js.replace(r'!!window.Script', 'false').replace(';!function()',
                                                         'function run()')
    js = js[:-3]
    eleven = ph_runtime.compile(js).call('run')
    return eleven
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
                elif source in 'daodao':
                    headers = {
                        'referer': 'https://www.tripadvisor.cn/',
                        'x-requested-with': 'XMLHttpRequest',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept': 'text/javascript, text/html, application/xml, text/xml, */*',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'Origin': 'https://www.tripadvisor.cn',
                        'Host': 'www.tripadvisor.cn'
                    }
                    url = source_interface[source]
                    response = session.post(
                        url=url,
                        headers=headers,
                        data={
                            'action': 'API',
                            'uiOrigin': 'PTPT-dest',
                            'types': 'geo,dest',
                            'hglt': True,
                            'global': True,
                            'legacy_format': True,
                            '_ignoreMinCount': True,
                            'query': keyword
                        }
                    )
                    get_suggest = getattr(sys.modules[__name__], 'get_{0}_suggest'.format(source))
                elif source in 'qyer':
                    headers = {
                        "Referer": "http://www.qyer.com/",
                        "Host": "www.qyer.com",
                    }
                    url = source_interface[source].format(keyword)
                    response = session.get(url,headers=headers)
                    get_suggest = getattr(sys.modules[__name__], 'get_{0}_suggest'.format(source))
                elif source in 'ctrip':
                    headers = {
                        'Accept-Encoding': 'gzip, deflate',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Referer': 'http://hotels.ctrip.com/international/',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
                        'Connection': 'keep-alive'
                    }
                    url = source_interface[source].format(keyword)
                    response = session.get(url, headers=headers)
                    get_suggest = getattr(sys.modules[__name__], 'get_{0}_suggest'.format(source))
                else:
                    url = source_interface[source].format(keyword)
                    response = session.get(url=url,)
                    get_suggest = getattr(sys.modules[__name__],'get_{0}_suggest'.format(source))

                count = get_suggest(response.content,map_info,country_id,city_id,database_name,keyword)
                if count >= 0:
                    self.task.error_code = 0
            except Exception as e:
                print(e)
                raise ServiceStandardError(ServiceStandardError.REQ_ERROR,wrapped_exception=e)

        return count

if __name__ == "__main__":
    args = {
        'keyword': '纽约',
        'source': 'booking',
        'map_info': '0.0',
        'country_id':'501',
        'city_id': '10002',
        'database_name': 'Cityupline'
    }
    task = Task(_worker='', _task_id='demo', _source='hotels', _type='supplement_field',
                _task_name='all_hotels_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='supplement_field',
                _routine_key='supplement_field', list_task_token='test', task_type=0, collection='')
    normal = AllHotelSourceSDK(task)
    normal.execute()
