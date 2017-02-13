#!/usr/bin/env python
# encoding:utf-8


import sys
from pprint import pprint
from pdb import set_trace

from lxml import etree

from base_parse import save_html

reload(sys)
sys.setdefaultencoding("utf-8")


def parse_main_page():
    test_fn = "flickr_test.html"
    with open(test_fn, 'r') as test_file:
        html_page_str = test_file.read()

    html_page = etree.HTML(html_page_str)
    search_path = '//script[@class="modelExport"]/text()'
    script_area = html_page.xpath(search_path)
    if len(script_area):
        model_export_script = script_area[0]
        save_html(model_export_script)
    else:
        set_trace()
