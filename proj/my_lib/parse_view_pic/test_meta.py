#!/usr/bin/env python
# encoding: utf-8

import json
import sys
from pdb import set_trace

from lxml import etree

reload(sys)
sys.setdefaultencoding("utf-8")

if __name__ == "__main__":
    html_fn = "1484102492.html"
    meta_xpath = '//*[@id="rso"]'
    with open(html_fn, "r") as html_file:
        html_str = html_file.read()
    html_page = etree.HTML(html_str.decode("utf-8"))
    pic_meta_list = html_page.xpath(meta_xpath)
    print len(pic_meta_list)
    for meta_item in pic_meta_list:
        pic_meta = json.loads(meta_item)
        print pic_meta.keys()
        set_trace()
