#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/18 下午1:56
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_crawl_report.py
# @Software: PyCharm
#统计酒店数目，生成csv文件。
import pandas
from sqlalchemy.engine import create_engine


def generate_report():
    sql = '''SELECT
  country.name,
  city.name,
  city_id,
  source,
  count(*)
FROM hotel_final_20170102a
  JOIN base_data.city ON hotel_final_20170102a.city_id = base_data.city.id
  JOIN base_data.country ON base_data.city.country_id = base_data.country.mid
WHERE source = 'accor'
GROUP BY base_data.city.id;'''
    engine = create_engine('mysql+pymysql://mioji_admin:mioji1109@10.10.228.253/BaseDataFinal?charset=utf8')
    table = pandas.read_sql(sql=sql, con=engine)
    new_table = None
    count_key_set = set()
    for key, sub_table in table.groupby(by=['source']):
        this_sub_table = sub_table.copy()
        del this_sub_table['source']
        count_key = '{}_num'.format(key)
        this_sub_table[count_key] = this_sub_table['count(*)']
        del this_sub_table['count(*)']
        count_key_set.add(count_key)

        if new_table is None:
            new_table = this_sub_table
        else:
            new_table = new_table.merge(this_sub_table, how='outer', on='city_id')

    new_table.fillna(0, inplace=True)
    new_table['total'] = sum([new_table[count_key] for count_key in count_key_set])
    return new_table

table = generate_report()
table.to_csv('/Users/zhangxiaopeng/Desktop/accor_crawled_report.csv')
# table
