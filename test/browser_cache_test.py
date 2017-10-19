#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/21 上午10:34
# @Author  : Hou Rong
# @Site    : 
# @File    : browser_cache_test.py
# @Software: PyCharm
from __future__ import print_function
from proj.my_lib.Common.Browser import MySession

if __name__ == '__main__':
    # baidu cache
    with MySession(need_proxies=False, auto_update_host=False, need_cache=True) as session:
        resp = session.get('http://www.baidu.com')
        # print(resp.text)

    # use baidu cache and delete them, cause of the exception
    try:
        with MySession(need_proxies=False, auto_update_host=False, need_cache=True) as session:
            resp = session.get('http://www.baidu.com')
            # print(resp.text)
            raise Exception()
    except Exception:
        pass
    # multi redirect test
    with MySession(need_proxies=False, need_cache=True) as session:
        resp = session.get('http://hilton.com.cn/zh-cn/city/Suzhou-hotels.html')
        # print(resp.text)

    # multi redirect test get cache
    with MySession(need_proxies=False, need_cache=True) as session:
        resp = session.get('http://hilton.com.cn/zh-cn/city/Suzhou-hotels.html')
        # print(resp.text)

    with MySession(need_proxies=True, need_cache=False) as session:
        resp = session.get('http://www.baidu.com')
        # print(resp.text)
    try:
        with MySession(need_proxies=False, auto_update_host=False, need_cache=True,
                       do_not_delete_cache=True) as session:
            resp = session.get('http://www.baidu.com')
            # print(resp.text)
            raise Exception()
    except Exception:
        pass
