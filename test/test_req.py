#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/23 下午5:24
# @Author  : Hou Rong
# @Site    : 
# @File    : test_req.py
# @Software: PyCharm
from proj.my_lib.Common.Browser import MySession

with MySession(need_proxies=True, need_cache=True, do_not_delete_cache=True,
               cache_expire_time=999999999) as session:
    session.get("http://www.baidu.com")
    resp = session.get(
        'http://www.booking.com/hotel/fr/trianonpalacehotelspa.zh-cn.html?aid=376390;label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-11455299683%3Alp9061505%3Ali%3Adec%3Adm;sid=114648ac01e63f9a40fee61cb2174c74;checkin=2017-11-18;checkout=2017-11-19;ucfs=1;srpvid=c89551c8ae630045;srepoch=1507203474;highlighted_blocks=5101834_99234382_2_42_0;all_sr_blocks=5101834_99234382_2_42_0;room1=A%2CA;hpos=12;hapos=12;dest_type=city;dest_id=-1475811;srfid=624e1ddf11c8ed1a3846e1c5ec818fcee9c6e4e1X12;from=searchresults;highlight_room=#hotelTmpl')

    # print(resp.content)
    content = resp.content
    print("Hello World")