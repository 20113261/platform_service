#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/7 下午4:46
# @Author  : Hou Rong
# @Site    : 
# @File    : full_website_parser.py
# @Software: PyCharm
import re


def full_website_parser(content, host_url):
    # css background-image 爬取
    for link in re.findall('background-image:url\(([\s\S]+?)\);', content):
        # if link.
        pass

    pass


if __name__ == '__main__':
    import requests

    url = 'https://www.alhambradegranada.org/zh/info/%E5%8D%A1%E6%B4%9B%E6%96%AF%E4%BA%94%E4%B8%96%E7%9A%87%E5%AE%AB%E5%8F%8A%E5%A4%96%E5%9B%B4/%E5%8D%A1%E6%B4%9B%E6%96%AF%E4%BA%94%E4%B8%96%E7%9A%87%E5%AE%AB.asp'
    page = requests.get(url)
    content = page.text
    full_website_parser(content)
