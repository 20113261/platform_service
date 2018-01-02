#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/10 下午9:42
# @Author  : Hou Rong
# @Site    : 
# @File    : test_google_address.py
# @Software: PyCharm
import sys

sys.path.append('/data/lib')
from proj.my_lib.Common.NetworkUtils import google_get_map_info

if __name__ == '__main__':
    # res = google_get_map_info('Avenida San Martin 249, El Chalten Z9301ABA, Argentina')
    # print(res)
    print(google_get_map_info('US, CARMEL, CA'))
    print(google_get_map_info('US, CARMEL, CA, CARMEL, CA'))
