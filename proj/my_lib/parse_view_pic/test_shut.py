#!/usr/bin/env python
# encoding:utf-8

from pdb import set_trace
import sys

from lxml import etree

reload(sys)
sys.setdefaultencoding("utf-8")


if __name__ == "__main__":
    test_fn = "test_shut.html"
    with open(test_fn, 'r') as test_file:
        html_str = test_file.read()
    html_page = etree.HTML(html_str)
    img_path = "//img[@src][@alt][name(..)='div'][../@class='img-wrap']"
    search_ret = html_page.xpath(img_path)
    img_link_list = []
    print len(search_ret)
    big_img_url = "https://image.shutterstock.com/z/"
    for item in search_ret:
        html_link = item.get('src')
        thumb_link = "https:" + html_link
        big_link = big_img_url + html_link.split("/")[-1]
        print thumb_link
        print big_link
        set_trace()
