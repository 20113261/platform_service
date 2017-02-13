#!/usr/bin/env python
# encoding:utf-8

import sys
from pdb import set_trace
from pprint import pprint

from base_parse import GooglePicSpider
from mysql_ext import PicModel
from pic_data_assembly import google_pic_data_assembly


reload(sys)
sys.setdefaultencoding("utf-8")


test_db_config = {"host": "10.10.9.184",
                  "user": "root",
                  "passwd": "Mioji2016-=",
                  "db": "spider_pic",
                  "charset": "utf8"}


if __name__ == "__main__":
    kw = "埃菲尔铁塔"
    proxy = None
    debug = True
    spider = GooglePicSpider(kw, proxy, debug)
    pic_ret = spider.pic_search()
    pprint(pic_ret)
    vid = "v0001"
    pic_save_data = google_pic_data_assembly(vid, kw, pic_ret)
    pprint(pic_save_data)
    set_trace()
    spider_db = PicModel(**test_db_config)
    thumb_table = pic_save_data["thumb"]["table"]
    fields = pic_save_data["thumb"]["fields"]
    data = pic_save_data["thumb"]["values"]
    spider_db.insert_pic_many(thumb_table, fields, data)
