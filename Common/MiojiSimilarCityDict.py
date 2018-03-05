#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/13 下午2:38
# @Author  : Hou Rong
# @Site    : 
# @File    : MiojiSimilarCityDict.py
# @Software: PyCharm
import pandas
import dataset
import unittest
import datetime
from collections import defaultdict
from Common.Utils import is_legal

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


class MiojiSimilarCityDict(object):
    def __init__(self,config):
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

    def get_keys(self, __line):
        country_key_set = set()
        city_key_set = set()
        region_key_set = set()

        additional_key = ADDITIONAL_COUNTRY_LIST.get(__line['country_id'], None)
        if additional_key is not None:
            country_key_set.add(key_modify(additional_key))

        for key in COUNTRY_KEYS:
            if is_legal(__line[key]):
                country_key_set.add(key_modify(__line[key]))

        for key in COUNTRY_MULTI_KEYS:
            if __line[key]:
                for word in __line[key].strip().split(MULTI_SPLIT_KEY):
                    if is_legal(word):
                        country_key_set.add(key_modify(word))

        if NEED_REGION:
            for key in REGION_KEY:
                if is_legal(__line[key]):
                    region_key_set.add(key_modify(__line[key]))

        for key in CITY_KEYS:
            if is_legal(__line[key]):
                city_key_set.add(key_modify(__line[key]))

        for key in CITY_MULTI_KEYS:
            if __line[key]:
                for word in __line[key].strip().split(MULTI_SPLIT_KEY):
                    if is_legal(word):
                        city_key_set.add(key_modify(word))

        # 保存 city_info 以便查询
        self.city_info_dict[__line['id']] = 'CityId ({3}) Country ({0}) Region ({1}) City ({2})'.format(
            ', '.join(country_key_set),
            ', '.join(region_key_set),
            ', '.join(city_key_set), __line['id'])

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
        __dict = defaultdict(set)
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
        for __line in city_country_info:
            for key in self.get_keys(__line):
                __dict[key].add(__line['id'])

        return __dict

    @staticmethod
    def modify_keys(keys):
        if KEY_TYPE == 'tuple':
            keys = tuple([k.lower() for k in keys])
        elif KEY_TYPE == 'str':
            keys = keys.lower()
        else:
            raise TypeError('未知分割类型，当前支持 str, tuple')

        return keys

    def get_mioji_city_info(self, city_id):
        return self.city_info_dict[str(city_id)]

    def get_mioji_city_id(self, keys,config):
        keys = self.modify_keys(keys)
        result, match_type = self._get_mioji_city_id(keys)
        self.report_data.append((keys, match_type, result))
        return result

    def _get_mioji_city_id(self, keys):
        keys = self.modify_keys(keys)
        result = set()
        match_type = "未匹配"
        if keys in self.dict:
            match_type = "直接获取"
            result = self.dict[keys]
            return result, match_type

        if NEED_REGION:
            if not self.can_use_mioji_region((keys[0], keys[-1])):
                if (keys[0], keys[-1]) in self.dict:
                    match_type = "region 降级，严格模式"
                    result = self.dict[(keys[0], keys[-1])]
                    return result, match_type

            if (keys[0], keys[-1]) in self.dict:
                match_type = "region 降级，非严格模式"
                result = self.dict[(keys[0], keys[-1])]
                return result, match_type

        return result, match_type


class SimilarCityDictTest(unittest.TestCase):
    def test_case_1(self):
        d = MiojiSimilarCityDict()
        self.assertSetEqual(d.get_mioji_city_id(('法国', 'paris')), {'10001', })

    def test_case_2(self):
        COUNTRY_KEYS.append('country_code')
        d = MiojiSimilarCityDict()
        self.assertSetEqual(d.get_mioji_city_id(('fr', 'paris')), {'10001', })

    def test_case_3(self):
        d = MiojiSimilarCityDict()
        self.assertSetEqual(d.get_mioji_city_id(('美国', '阿森斯')), {'50251', '50252'})

    def test_case_4(self):
        global COUNTRY_KEYS
        COUNTRY_KEYS = ['country_id', 'country_name', 'country_name_en', 'country_short_name_cn',
                        'country_short_name_en']
        d = MiojiSimilarCityDict()
        self.assertSetEqual(d.get_mioji_city_id(('501', '阿森斯')), {'50251', '50252'})

    def test_case_5(self):
        global COUNTRY_KEYS
        COUNTRY_KEYS.append('country_id')
        global NEED_REGION
        NEED_REGION = True
        global REGION_KEY
        REGION_KEY.append('prov_id')
        d = MiojiSimilarCityDict()
        self.assertSetEqual(d.get_mioji_city_id(('501', 'p501019', '斯普林菲尔德')), {'50815', })

    def test_case_6(self):
        d = MiojiSimilarCityDict()
        self.assertSetEqual(d.get_mioji_city_id(('新西兰', '皇后镇')), {'30095', })

    def test_case_7(self):
        d = MiojiSimilarCityDict()
        self.assertSetEqual(d.get_mioji_city_id(('usa', 'anaheim')), {'50245'})
        self.assertSetEqual(d.get_mioji_city_id(('usa', '123123123123', 'anaheim')), {'50245'})
        self.assertSetEqual(d.get_mioji_city_id(('usa', '123123123123', '1123123123123')), set())


if __name__ == '__main__':
    unittest.main()
