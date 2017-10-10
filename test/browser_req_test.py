#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/10 下午7:46
# @Author  : Hou Rong
# @Site    : 
# @File    : browser_req_test.py
# @Software: PyCharm
from proj.my_lib.Common.Browser import MySession

if __name__ == '__main__':
    with MySession(need_proxies=True) as session:
        session.get('http://www.baidu.com')
