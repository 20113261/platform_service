#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/7 下午4:46
# @Author  : Hou Rong
# @Site    : 
# @File    : full_website_parser.py
# @Software: PyCharm
from urlparse import urljoin, urlparse

import re
import pyquery


def url_is_legal(url):
    return bool(re.match(r'^https?:/{2}\w.+$', url or ''))


def full_website_parser(content, url):
    # 存储已获得的 img url
    img_url_set = set()
    pdf_url_set = set()
    next_url_set = set()

    # css background-image 爬取
    for link in re.findall('background-image:url\(([\s\S]+?)\);', content):
        new_link = urljoin(url, link.strip('\'').strip())
        img_url_set.add(new_link)

    doc = pyquery.PyQuery(content)
    doc.make_links_absolute(url)

    for item in doc('img').items():
        img_url_set.add(item.attr.src)

    for item in doc('a').items():
        if url_is_legal(item.attr.href):
            # pdf 入 pdf set
            if item.attr.href.lower().endswith('pdf'):
                pdf_url_set.add(item.attr.href)
            # 图像入 img set
            elif any(map(lambda x: item.attr.href.lower().strip().endswith(x), ['.bmp', '.jpeg', '.jpg', '.gif', '.png', '.svg'])):
                img_url_set.add(item.attr.href)
            # 剩余无法判断的应该是 html 页面，进行下一次抓取
            elif urlparse(item.attr.href).netloc == urlparse(url).netloc:
                next_url_set.add(item.attr.href)

    return img_url_set, pdf_url_set, next_url_set


if __name__ == '__main__':
    import requests

    # url = 'https://www.alhambradegranada.org/zh/info/%E5%8D%A1%E6%B4%9B%E6%96%AF%E4%BA%94%E4%B8%96%E7%9A%87%E5%AE%AB%E5%8F%8A%E5%A4%96%E5%9B%B4/%E5%8D%A1%E6%B4%9B%E6%96%AF%E4%BA%94%E4%B8%96%E7%9A%87%E5%AE%AB.asp'
    url = 'http://www.parcjeandrapeau.com'
    page = requests.get(url)
    content = page.text
    page.headers['Content-type']
    # 用于判断是否为 html 或者其他文件
    print full_website_parser(content, url)
