#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/10 下午7:46
# @Author  : Hou Rong
# @Site    : 
# @File    : browser_req_test.py
# @Software: PyCharm
from proj.my_lib.Common.Browser import MySession

if __name__ == '__main__':
    # with MySession(need_proxies=True) as session:
    #     session.get('http://www.baidu.com')
    import time

    # target_url = "http://pic.qyer.com/album/user/1329/11/QEpXSxsGYUo/index"
    # with MySession(need_cache=False, need_proxies=True) as session:
    #     start = time.time()
    #     _resp = session.get(url=target_url)
    #     print("raw takes", time.time() - start)
    #
    #     start = time.time()
    #     _resp = session.get(url=target_url, stream=True)
    #     _f_content = b''
    #     _count = 0
    #     for chunk in _resp.iter_content(chunk_size=1024):
    #         _count += 1
    #         print(_count)
    #         if chunk:
    #             _f_content += chunk
    #             # print(_f_content)
    #     print("stream takes", time.time() - start)
    with MySession(need_proxies=True, need_cache=True, do_not_delete_cache=True) as session:
        resp = session.get('http://place.qyer.com/poi/V2wJYVFvBzNTbQ/photo')
        print(resp.content)
