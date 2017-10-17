#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/17 下午9:09
# @Author  : Hou Rong
# @Site    : 
# @File    : elong_test.py
# @Software: PyCharm
from proj.my_lib.new_hotel_parser import elong_parser


# def test_elong_parser(page):
#     return elong_parser(page,
#                         url='',
#                         other_info={'source_id': 'test', 'city_id': 'test'}
#                         )


if __name__ == '__main__':
    from proj.my_lib.Common.Browser import MySession

    with MySession(need_cache=True) as session:
        page = session.get('http://ihotel.elong.com/367231/')
    result = page.text
    print(page.text)
