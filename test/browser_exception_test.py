#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/23 下午5:34
# @Author  : Hou Rong
# @Site    : 
# @File    : browser_exception_test.py
# @Software: PyCharm
from proj.my_lib.Common.Browser import MySession

if __name__ == '__main__':
    with MySession(need_proxies=False) as session:
        page = session.get('https://r-ec.bstatic.com/images/hotel/max1024x768/299/29970447.jpg', timeout=(120, None))
        print(page.text)
        flag = 1

    print(flag)
