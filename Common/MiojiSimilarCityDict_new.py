#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/13 下午2:38
# @Author  : Hou Rong
# @Site    :
# @File    : MiojiSimilarCityDict.py
# @Software: PyCharm
import pandas
import dataset
import datetime
from collections import defaultdict
from Common.Utils import is_legal
import numpy as np
#import unittest
# 相似多字段分割符
MULTI_SPLIT_KEY = '|'
# 从城市表中获取的字段
CITY_KEYS = ['name', 'name_en']
# 从城市表中获取的多字段，中间用 MULTI_SPLIT_KEY 分割
CITY_MULTI_KEYS = ['alias']
# 从国家表中获取的字段
COUNTRY_KEYS = ['country_name', 'country_name_en', 'country_short_name_cn', 'country_short_name_en']
# 从国家表中获取的多字段，中间用 MULTI_SPLIT_KEY 分割
COUNTRY_MULTI_KEYS = ['country_alias']
# 是否使用 Region 做 key 进行匹配
NEED_REGION = True
# region 匹配严格方法，如果我方城市有 region 且带 region 没有匹配，则返回空
# region 匹配非严格方法，优先进行 region 匹配，如果没有匹配到，自动降级为国家，城市匹配
# 优先使用严格方法匹配，如无匹配，则使用非严格方法匹配
# Region 使用的字段
REGION_KEY = ['region', 'region_en', 'region_cn']

# 字典的 key 类型，可与选择 tuple 和 str 类型
KEY_TYPE = 'tuple'
# 当 key 类型为 str 时，多值生成 key 中间所使用的分割符
STR_KEY_SPLIT_WORD = '|'
# 字典 key 内容
# both 用国家城市做 key
# city 只用 city 信息做 key
KEY_CONTENT = 'both'

# 额外补充的国家 mid 对应关系, {'mid':'country'}
ADDITIONAL_COUNTRY_LIST = {}


def key_modify(s):
    return s.strip().lower()


class c_obj(object):
    def __init__(self,cid,name,map_info,name_en,country_code,country_name,dis=None):
        self.cid = cid
        self.name = name
        self.map_info = map_info
        self.name_en = name_en
        self.country_code = country_code
        self.country_name = country_name
        self.dis = dis


class MiojiSimilarCityDict(object):
    def __init__(self,config):
        self.config = config
        self.can_use_region = defaultdict(bool)
        self.city_info_dict = defaultdict(str)
        self.dict = self.get_mioji_similar_dict(config)
        self.report_data = []

    def __del__(self):
        # 当程序退出时候，打印报表
        # (keys, match_type, result)
        csv_file_name = datetime.datetime.now().strftime("./city_match_report_%Y_%m_%d_%H_%M_%S.csv")
        table = pandas.DataFrame(data=self.report_data, columns=["keys", "match_type", "result"])
        table.to_csv(csv_file_name)

    def get_keys(self, _line):
        country_key_set = set()
        city_key_set = set()
        region_key_set = set()

        additional_key = ADDITIONAL_COUNTRY_LIST.get(_line['country_id'], None)
        if additional_key is not None:
            country_key_set.add(key_modify(additional_key))

        for key in COUNTRY_KEYS:
            if is_legal(_line[key]):
                country_key_set.add(key_modify(_line[key]))

        for key in COUNTRY_MULTI_KEYS:
            if _line[key]:
                for word in _line[key].strip().split(MULTI_SPLIT_KEY):
                    if is_legal(word):
                        country_key_set.add(key_modify(word))

        if NEED_REGION:
            for key in REGION_KEY:
                if is_legal(_line[key]):
                    region_key_set.add(key_modify(_line[key]))

        for key in CITY_KEYS:
            if is_legal(_line[key]):
                city_key_set.add(key_modify(_line[key]))

        for key in CITY_MULTI_KEYS:
            if _line[key]:
                for word in _line[key].strip().split(MULTI_SPLIT_KEY):
                    if is_legal(word):
                        city_key_set.add(key_modify(word))

        # 保存 city_info 以便查询
        self.city_info_dict[_line['id']] = 'CityId ({3}) Country ({0}) Region ({1}) City ({2})'.format(
            ', '.join(country_key_set),
            ', '.join(region_key_set),
            ', '.join(city_key_set), _line['id'])

        if KEY_CONTENT == 'both':
            if NEED_REGION:
                for country in country_key_set:
                    for region in region_key_set:
                        for city in city_key_set:
                            if KEY_TYPE == 'tuple':
                                yield country, region, city
                            elif KEY_TYPE == 'str':
                                yield STR_KEY_SPLIT_WORD.join([country, region, city])
                            else:
                                raise TypeError('未知分割类型，当前支持 str, tuple')

            for country in country_key_set:
                for city in city_key_set:
                    if NEED_REGION:
                        if len(region_key_set) > 0:
                            self.can_use_region[(country, city)] = True

                    if KEY_TYPE == 'tuple':
                        yield country, city
                    elif KEY_TYPE == 'str':
                        yield STR_KEY_SPLIT_WORD.join([country, city])
                    else:
                        raise TypeError('未知分割类型，当前支持 str, tuple')

        elif KEY_CONTENT == 'city':
            for city in city_key_set:
                yield city
        else:
            raise TypeError('未知 key 内容设置')

    def can_use_mioji_region(self, keys):
        return self.can_use_region[keys]

    def get_mioji_similar_dict(self,config):
        _dict = defaultdict(set)
        #db_test = dataset.connect('mysql+pymysql://reader:miaoji1109@10.10.69.170/base_data?charset=utf8')
        db_test = dataset.connect('mysql+pymysql://{user}:{password}@{host}/{db}?charset={charset}'.format(**config),
                                  reflect_views=False)
        city_country_info = [
            i for i in db_test.query('''SELECT
  city.id,
  city.name,
  city.name_en,
  city.alias,
  city.tri_code,
  province.name           AS region,
  province.name           AS region_cn,
  province.name_en        AS region_en,
  city.prov_id,
  country.mid           AS country_id,
  country.country_code,
  country.name          AS country_name,
  country.name_en       AS country_name_en,
  country.alias         AS country_alias,
  country.short_name_cn AS country_short_name_cn,
  country.short_name_en AS country_short_name_en
FROM city
  JOIN country ON city.country_id = country.mid
  LEFT JOIN province ON prov_id = province.id;''')
        ]
        for _line in city_country_info:
            for key in self.get_keys(_line):
                _dict[key].add(_line['id'])
        return _dict

    @staticmethod
    def modify_keys(keys):
        if KEY_TYPE == 'tuple':
            keys = tuple([k.strip().lower() for k in keys])
        elif KEY_TYPE == 'str':
            keys = keys.lower()
        else:
            raise TypeError('未知分割类型，当前支持 str, tuple')
        return keys


    @staticmethod
    def get_distance(c_map_info, p_map_info):
        try:
            c_lon, c_lat = c_map_info.split(',')
            p_lon, p_lat = p_map_info.split(',')
            lat1, lon1, lat2, lon2 =  float(c_lat), float(c_lon), float(p_lat), float(p_lon)
            R = 6371  # Earth radius in km
            d_lat = np.radians(lat2 - lat1)
            d_lon = np.radians(lon2 - lon1)
            r_lat1 = np.radians(lat1)
            r_lat2 = np.radians(lat2)
            a = np.sin(d_lat / 2.) ** 2 + np.cos(r_lat1) * np.cos(r_lat2) * np.sin(d_lon / 2.) ** 2
            haversine = 2 * R * np.arcsin(np.sqrt(a))
            return haversine  #return dist_from_coordinates(float(c_lat), float(c_lon), float(p_lat), float(p_lon))
        except:
            pass
        return -1

    @staticmethod
    def get_obj_lis(cid,config):
        db_test = dataset.connect('mysql+pymysql://{user}:{password}@{host}/{db}?charset={charset}'.format(**config),
                                  reflect_views=False)
        sql_res = db_test.query('''SELECT

                          city.name,
                          city.map_info,
                          city.name_en,     
                          city.alias,
                          city.tri_code,
                          province.name           AS region,
                          province.name           AS region_cn,
                          province.name_en        AS region_en,
                          city.prov_id,
                          country.mid           AS country_id,
                          country.country_code,
                          country.name          AS country_name,
                          country.name_en       AS country_name_en,
                          country.alias         AS country_alias,
                          country.short_name_cn AS country_short_name_cn,
                          country.short_name_en AS country_short_name_en
                        FROM city
                          JOIN country ON city.country_id = country.mid
                          LEFT JOIN province ON prov_id = province.id WHERE city.id = '%s';''' % cid)
        return sql_res

    def get_mioji_city_info(self, city_id):
        return self.city_info_dict[str(city_id)]

    def get_mioji_city_id(self, keys,map = None,config=None):
        keys = self.modify_keys(keys)
        result, match_type = self._get_mioji_city_id(keys,config)
        if map:
            c_map_info = map
            lis = []
            lis0 = []
            rename_lis = []
            for i in result:
                p_map_info = i.map_info
                dis = self.get_distance(c_map_info, p_map_info)
                i.dis = dis
                if keys[-1] == i.name or keys[-1] == i.name_en.lower():
                    if len(result) > 1 and 0 <= dis <= 30:
                        rename_lis.append(i)
                    elif 0 <= dis <= 20:
                        rename_lis.append(i)
                else:
                    if 0 <= dis <= 20:
                        lis0.append(i)
                #print ('cs')
            rename_lis = sorted(rename_lis, key=lambda x: x.dis) if rename_lis else []
            lis0 = sorted(lis0, key=lambda x: x.dis) if lis0 else []
            for temp1 in rename_lis:
                lis.append(temp1)
            for temp2 in lis0:
                lis.append(temp2)
            if lis:
                for i in lis:
                    self.report_data.append((keys, match_type, (i.cid,i.name,i.name_en,i.map_info,i.dis,i.country_code,i.country_name)))
            return lis
        for i in result:
            self.report_data.append((keys, match_type,(i.cid,i.name,i.name_en,i.map_info,i.dis,i.country_code,i.country_name)))
        return result

    def _get_mioji_city_id(self, keys,config):
        lis = []
        keys = self.modify_keys(keys)
        result = set()
        match_type = "未匹配"

        if keys not in self.dict:
            if '(' in keys[-1]:
                num = 0
                for i in keys[-1]:
                    num += 1
                    if i == '(' and (keys[-1][num]!='省' and keys[-1][num]!='郡'):
                        keys = (keys[0], keys[-1][:num - 1].strip())

            if keys[0] == '日本' or keys[0] == '美国':
                if keys[-1][-1] == '市':
                    if (keys[0], keys[-1][:-1]) in self.dict:
                        keys = (keys[0], keys[-1][:-1])
                elif (keys[0], keys[-1] + '市') in self.dict:
                    keys = (keys[0], keys[-1] + '市')
            elif keys[-1][-1] == '市' or keys[-1][-1] == '县':
                if (keys[0], keys[-1][:-1]) in self.dict:
                    keys = (keys[0], keys[-1][:-1])
            elif (keys[0], keys[-1] + '市') in self.dict:
                keys = (keys[0], keys[-1] + '市')
            elif (keys[0], keys[-1] + '县') in self.dict:
                keys = (keys[0], keys[-1] + '县')

        if keys in self.dict:
            temp = []
            match_type = "直接获取"
            result = self.dict[keys]

            for j in list(result):
                sql_res = self.get_obj_lis(j,config)
                for jid in sql_res:
                    jid['id'] = j
                    name = jid.get('name')
                    cid = jid.get('id')
                    map_info = jid.get('map_info')
                    name_en = jid.get('name_en')
                    country_code = jid.get('country_code')
                    country_name = jid.get('country_name')
                    obj = c_obj(cid,name,map_info,name_en,country_code,country_name,dis=None)
                    lis.append(obj)
            return lis, match_type

        if NEED_REGION:
            if not self.can_use_mioji_region((keys[0], keys[-1])):
                if (keys[0], keys[-1]) in self.dict:
                    match_type = "region 降级，严格模式"
                    result = self.dict[(keys[0], keys[-1])]
                    sql_res = self.get_obj_lis(list(result)[0],config)
                    for i in sql_res:
                        s_res = i
                        name = s_res.get('name')
                        cid = s_res.get('id')
                        map_info = s_res.get('map_info')
                        name_en = s_res.get('name_en')
                        country_code = s_res.get('country_code')
                        country_name = s_res.get('country_name')
                        obj = c_obj(cid, name, map_info, name_en, country_code, country_name)
                        lis.append(obj)
                    return lis, match_type

            if (keys[0], keys[-1]) in self.dict:
                match_type = "region 降级，非严格模式"
                result = self.dict[(keys[0], keys[-1])]
                sql_res = self.get_obj_lis(list(result)[0],config)
                for i in sql_res:
                    s_res = i
                    name = s_res.get('name')
                    cid = s_res.get('id')
                    map_info = s_res.get('map_info')
                    name_en = s_res.get('name_en')
                    country_code = s_res.get('country_code')
                    country_name = s_res.get('country_name')
                    obj = c_obj(cid, name, map_info, name_en, country_code, country_name, dis=None)
                    lis.append(obj)
                return lis, match_type
        return result, match_type


if __name__ == '__main__':
    d = MiojiSimilarCityDict()
    COUNTRY_KEYS = ['country_id', 'country_name', 'country_name_en', 'country_short_name_cn','country_short_name_en']
    print(d.get_mioji_city_id(('Jordan', 'Wadi Musa'),'35.4832992553711,30.3166999816895')[0].cid)
    print(d.get_mioji_city_id(('意大利', '塔兰托(省)')))
    print(d.get_mioji_city_id(('约旦', '安曼 (及邻近地区)'))[0].cid)
    print(d.get_mioji_city_id(('日本','大阪县')))#"2.35147638246417,48.8566821749061")[0].cid)
    print(d.get_mioji_city_id(('中国', '达县县'))[0].cid)
    for map in ["115.041500091553,-8.45612507720947","115.210892,-8.273642","115.222,-8.656","115.22156,-8.65667","115.111241,-8.380058","115.188916,-8.409518"]:
        kk = d.get_mioji_city_id(('印度尼西亚', '巴厘岛'), map)
        print (kk[0].cid,kk[0].name,kk[0].map_info,map,kk[0].dis if kk else kk)
