#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/20 下午2:27
# @Author  : Hou Rong
# @Site    : 
# @File    : get_cached_page.py
# @Software: PyCharm
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.new_hotel_parser.ctrip_parser import ctrip_parser
from proj.my_lib.new_hotel_parser.booking_parser import booking_parser


def test():
    with MySession(need_cache=True, do_not_delete_cache=True, cache_expire_time=60 * 60 * 24 * 90) as session:
        # resp = session.get('http://hotels.ctrip.com/international/992466.html')
        resp = session.get("http://www.booking.com/hotel/jp/st-regis-osaka.zh-cn.html?aid=376390;label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-11455299683%3Alp9061505%3Ali%3Adec%3Adm;sid=9e4dd9683b98b4704893d0365aacdb0f;checkin=2017-11-18;checkout=2017-11-19;ucfs=1;aer=1;srpvid=b39a5688521100a0;srepoch=1507205905;highlighted_blocks=38198816_94453559_2_2_0;all_sr_blocks=38198816_94453559_2_2_0;room1=A%2CA;hpos=8;hapos=638;dest_type=city;dest_id=-243223;srfid=7d0eb6fbb0301135b09f1c72a45d7c9cf6bed8ecX638;from=searchresults;highlight_room=;spdest=ci/-243223;spdist=68.4#hotelTmpl")
        # print(resp.content)
        hotel = booking_parser(content=resp.content, url='', other_info={'source_id': '', 'city_id': ''})
    # hotel = ctrip_parser(page=resp.content, url='', other_info={'source_id': '', 'city_id': ''})
    #
    print(hotel.hotel_name)
    print(hotel.hotel_name_en)


if __name__ == '__main__':
    test()
