#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import urllib
import operator
import json
from math import *
import mioji.common.suggestion as suggestion


def get_postdata(html_text):
    condition = re.search("condition\s*=\s*'([^']+)'", html_text).group(1)
    try:
        searchkey = json.loads(condition)['SearchKey']
    except:
        searchkey = json.loads(condition, encoding='gb2312')['SearchKey']

    res = re.search(r'var\s+(\w+)\s*=1\s*,\s*(\w+)\s*=\s*1', html_text).groups()
    v1_name, v2_name = res
    v1 = v2 = 1

    op_dict = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.div}
    regexp_t = "{var}\s*=\s*{var}\s*([*/+-])=\s*eval.*?'(\w+\|\w+\|\w+\|\w+\|\w+)'"
    pat_eval = re.compile('\w+\|\w+\|(\w+)\|(\w+)\|(\w+)')
    # v1
    pat_process1 = re.compile(regexp_t.format(var=v1_name), re.S)
    process1 = pat_process1.findall(html_text)
    for op, val in process1:
        to_eval = pat_eval.sub(r'\1(\3)*\2', val)
        v1 = op_dict[op](v1, int(eval(to_eval)))
    v1 = -v1 if v1 < 0 else v1
    while v1 > 30: v1 %= 10

    # v2
    pat_process2 = re.compile(regexp_t.format(var=v2_name), re.S)
    process2 = pat_process2.findall(html_text)
    for op, val in process2:
        to_eval = pat_eval.sub(r'\1(\3)*\2', val)
        v2 = op_dict[op](v2, int(eval(to_eval)))
    v2 = -v2 if v2 < 0 else v2
    while v2 > 30: v2 %= 10

    searchkey = list(searchkey)
    searchkey.insert(v1, searchkey.pop(v2))
    searchkey = ''.join(searchkey).encode()

    condition = re.sub('(?<="SearchKey":")[^"]+(?=")', searchkey, condition).encode('utf8')
    return condition
    # postdata = 'SearchMode=TokenSearch&condition={0}&SearchToken=1'.format(urllib.quote(condition, safe='()'))
    # return postdata


def get_city_no(cityid):
    if cityid in suggestion.suggestion['hnair']:
        return suggestion.suggestion['hnair'][cityid]
    raise AttributeError("出发地或者目的地有错误！")


def get_promotion(tip):  # tips里面有几项就会在网页上显示几项。现在只爬第一项的。到但是
    content = '特惠专享'
    if 'Type' in tip:
        if tip['Type'] == 'TEXT':
            content = tip['Text']
        elif tip['Type'] == 'BUSS':
            content = '商务优选'
        elif tip['Type'] == 'AIRLINE':
            content = tip['Content'] + "（航空公司官网）"
        elif tip['Type'] == 'STU':
            content = '留学生票'
        elif tip['Type'] == 'HUI':
            content = tip['Text'] if 'Text' in tip else tip['Content']
        else:
            pass
    return content


# ctrip 去重逻辑
def remove_duplicate(tickets):
    all_flights = {}
    for x in tickets:
        key = x[0] + '|' + x[13]
        if key not in all_flights:
            all_flights[key] = x
        elif all_flights[key][10] > x[10]:
            all_flights[key] = x
    ll = []
    for x in all_flights:
        ll += [all_flights[x]]
    return ll
