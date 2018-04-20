#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月11日

@author: dujun
'''

import urlparse
import urllib
url = 'http://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA&sid=856b717ff095a5294d897d227d9e7ef4&sb=1&src=index&src_elem=sb&error_url=http%3A%2F%2Fwww.booking.com%2Findex.zh-cn.html%3Flabel%3Dgen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA%3Bsid%3D856b717ff095a5294d897d227d9e7ef4%3Bsb_price_type%3Dtotal%26%3B&ss=%E5%A1%94%E6%9E%97%2C+%E5%93%88%E5%B0%94%E5%B0%A4%E5%8E%BF%2C+%E7%88%B1%E6%B2%99%E5%B0%BC%E4%BA%9A&checkin_year=2017&checkin_month=3&checkin_monthday=3&checkout_year=2017&checkout_month=3&checkout_monthday=4&room1=A%2CA&no_rooms=1&group_adults=2&group_children=0&search_pageview_id=e22544b8c7f000c9&ac_suggestion_list_length=5&ac_suggestion_theme_list_length=0&ac_position=0&ac_langcode=zh&dest_id=-2625660&dest_type=city&search_pageview_id=e22544b8c7f000c9&search_selected=true&ss_raw=talin'
url = 'http://www.booking.com/hotel/ee/apartements-in-tallinn.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA;sid=856b717ff095a5294d897d227d9e7ef4;checkin=2017-03-03;checkout=2017-03-04;ucfs=1;soh=1;highlighted_blocks=;all_sr_blocks=;room1=A,A;soldout=0,0;hpos=1;dest_type=city;dest_id=-2625660;srfid=959574798018061c7f7a0ec9d0c19c3815d70e0dX1;highlight_room='

def params(url):
    pass

def encode_url(params):
    return urllib.urlencode(params)

if __name__ == '__main__':
    url = 'https://zh.hotels.com/search/listings.json?destination-id=504261&q-check-out=2017-02-16&q-destination=%E6%B3%95%E5%9C%8B,+%E5%B7%B4%E9%BB%8E&q-room-0-adults=2&pg=1&q-rooms=1&start-index=23&q-check-in=2017-02-15&resolved-location=CITY:504261:UNKNOWN:UNKNOWN&q-room-0-children=0&pn=3&callback=dio.pages.sha.searchResultsCallback'
    # url = 'https://zh.hotels.com/search.do?resolved-location=CITY%3A504261%3AUNKNOWN%3AUNKNOWN&destination-id=504261&q-destination=%E6%B3%95%E5%9C%8B,%20%E5%B7%B4%E9%BB%8E&q-check-in=2017-02-15&q-check-out=2017-02-16&q-rooms=1&q-room-0-adults=2&q-room-0-children=0'
    url = 'https://zh.hotels.com/search/listings.json?destination-id=504261&q-check-out=2017-02-16&q-destination=%E6%B3%95%E5%9C%8B,+%E5%B7%B4%E9%BB%8E&q-room-0-adults=2&pg=1&q-rooms=1&start-index=43&q-check-in=2017-02-15&resolved-location=CITY:504261:UNKNOWN:UNKNOWN&q-room-0-children=0&pn=5&callback=dio.pages.sha.searchResultsCallback'
    url = 'https://zh.hotels.com/search.do?resolved-location=CITY%3A504261%3AUNKNOWN%3AUNKNOWN&destination-id=504261&q-destination=%E6%B3%95%E5%9C%8B,%20%E5%B7%B4%E9%BB%8E&q-check-in=2017-02-15&q-check-out=2017-02-16&q-rooms=3&q-room-0-adults=2&q-room-0-children=0&q-room-1-adults=1&q-room-1-children=2&q-room-1-child-0-age=6&q-room-1-child-1-age=15&q-room-2-adults=2&q-room-2-children=2&q-room-2-child-0-age=0&q-room-2-child-1-age=3'
    
    url = 'http://www.booking.com/autocomplete_2?v=1&lang=zh-cn&sid=856b717ff095a5294d897d227d9e7ef4&aid=376390&pid=9bb13ce9aca502d0&stype=1&src=index&eb=4&e_obj_labels=1&at=1&e_tclm=1&e_smmd=2&e_ms=1&e_msm=1&e_themes_msm_1=1&add_themes=1&themes_match_start=1&include_synonyms=1&sort_nr_destinations=1&gpf=1&term=%E5%B7%B4%E9%BB%8E&_=1484556011691'
    url = 'http://www.booking.com/searchresults.zh-cn.html?aid=376390&label=bookings-naam-1gvwAanIQSGAF2rnkEExXAS144446357450%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-65526620%3Alp9061505%3Ali%3Adec%3Adm&sid=856b717ff095a5294d897d227d9e7ef4&sb=1&src=index&src_elem=sb&error_url=http%3A%2F%2Fwww.booking.com%2Findex.zh-cn.html%3Faid%3D376390%3Blabel%3Dbookings-naam-1gvwAanIQSGAF2rnkEExXAS144446357450%253Apl%253Ata%253Ap1%253Ap2%253Aac%253Aap1t1%253Aneg%253Afi%253Atikwd-65526620%253Alp9061505%253Ali%253Adec%253Adm%3Bsid%3D856b717ff095a5294d897d227d9e7ef4%3Bsb_price_type%3Dtotal%26%3B&ss=%E5%B7%B4%E9%BB%8E%2C+%E6%B3%95%E5%85%B0%E8%A5%BF%E5%B2%9B%E5%A4%A7%E5%8C%BA%2C+%E6%B3%95%E5%9B%BD&checkin_year=2017&checkin_month=1&checkin_monthday=20&checkout_year=2017&checkout_month=1&checkout_monthday=21&room1=A%2CA&no_rooms=1&group_adults=2&group_children=0&ss_raw=%E5%B7%B4%E9%BB%8E&ac_popular_badge=1&ac_position=0&ac_langcode=zh&dest_id=-1456928&dest_type=city&search_pageview_id=9bb13ce9aca502d0&search_selected=true'
    
    url = 'http://www.booking.com/searchresults.zh-cn.html?aid=376390&label=bookings-naam-1gvwAanIQSGAF2rnkEExXAS144446357450%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-65526620%3Alp9061505%3Ali%3Adec%3Adm&sid=856b717ff095a5294d897d227d9e7ef4&sb=1&src=searchresults&src_elem=sb&error_url=http%3A%2F%2Fwww.booking.com%2Fsearchresults.zh-cn.html%3Faid%3D376390%3Blabel%3Dbookings-naam-1gvwAanIQSGAF2rnkEExXAS144446357450%253Apl%253Ata%253Ap1%253Ap2%253Aac%253Aap1t1%253Aneg%253Afi%253Atikwd-65526620%253Alp9061505%253Ali%253Adec%253Adm%3Bsid%3D856b717ff095a5294d897d227d9e7ef4%3Bcheckin_month%3D1%3Bcheckin_monthday%3D20%3Bcheckin_year%3D2017%3Bcheckout_month%3D1%3Bcheckout_monthday%3D21%3Bcheckout_year%3D2017%3Bclass_interval%3D1%3Bdest_id%3D-1456928%3Bdest_type%3Dcity%3Bdtdisc%3D0%3Bgroup_adults%3D2%3Bgroup_children%3D0%3Bhlrd%3D0%3Bhyb_red%3D0%3Binac%3D0%3Blabel_click%3Dundef%3Bnha_red%3D0%3Bno_rooms%3D1%3Boffset%3D0%3Bpostcard%3D0%3Braw_dest_type%3Dcity%3Bredirected_from_city%3D0%3Bredirected_from_landmark%3D0%3Bredirected_from_region%3D0%3Broom1%3DA%252CA%3Bsb_price_type%3Dtotal%3Bsearch_selected%3D1%3Bsrc%3Dindex%3Bsrc_elem%3Dsb%3Bss%3D%25E5%25B7%25B4%25E9%25BB%258E%252C%2520%25E6%25B3%2595%25E5%2585%25B0%25E8%25A5%25BF%25E5%25B2%259B%25E5%25A4%25A7%25E5%258C%25BA%252C%2520%25E6%25B3%2595%25E5%259B%25BD%3Bss_all%3D0%3Bss_raw%3D%25E5%25B7%25B4%25E9%25BB%258E%3Bssb%3Dempty%3Bsshis%3D0%26%3B&ss=%E5%B7%B4%E9%BB%8E&ssne=%E5%B7%B4%E9%BB%8E&ssne_untouched=%E5%B7%B4%E9%BB%8E&city=-1456928&checkin_year=2017&checkin_month=1&checkin_monthday=20&checkout_year=2017&checkout_month=1&checkout_monthday=21&room1=A%2CA%2C3%2C0%2C12+&no_rooms=1&group_adults=2&group_children=3&age=3&age=0&age=12+&show_non_age_message=1'
    url = 'http://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA&sid=fe8d9421ac71bac5e9844293f1d6df29&sb=1&src=searchresults&src_elem=sb&error_url=http%3A%2F%2Fwww.booking.com%2Fsearchresults.zh-cn.html%3Flabel%3Dgen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA%3Bsid%3Dfe8d9421ac71bac5e9844293f1d6df29%3Bcheckin_month%3D1%3Bcheckin_monthday%3D20%3Bcheckin_year%3D2017%3Bcheckout_month%3D1%3Bcheckout_monthday%3D21%3Bcheckout_year%3D2017%3Bcity%3D-1456928%3Bclass_interval%3D1%3Bdtdisc%3D0%3Bgroup_adults%3D6%3Bgroup_children%3D0%3Bhlrd%3D0%3Bhyb_red%3D0%3Binac%3D0%3Blabel_click%3Dundef%3Bnha_red%3D0%3Bno_rooms%3D3%3Boffset%3D0%3Bpostcard%3D0%3Bredirected_from_city%3D0%3Bredirected_from_landmark%3D0%3Bredirected_from_region%3D0%3Broom1%3DA%252CA%3Broom2%3DA%252CA%3Broom3%3DA%252CA%3Bsb_price_type%3Dtotal%3Bsrc%3Dsearchresults%3Bsrc_elem%3Dsb%3Bss%3D%25E5%25B7%25B4%25E9%25BB%258E%3Bss_all%3D0%3Bssb%3Dempty%3Bsshis%3D0%3Bssne%3D%25E5%25B7%25B4%25E9%25BB%258E%3Bssne_untouched%3D%25E5%25B7%25B4%25E9%25BB%258E%26%3B&ss=%E5%B7%B4%E9%BB%8E&ssne=%E5%B7%B4%E9%BB%8E&ssne_untouched=%E5%B7%B4%E9%BB%8E&city=-1456928&checkin_year=2017&checkin_month=1&checkin_monthday=20&checkout_year=2017&checkout_month=1&checkout_monthday=21&room1=A%2CA%2CA%2CA%2CA%2CA%2C1%2C2&no_rooms=3&group_adults=6&group_children=2&age=1&age=2'
    
    url = 'https://www.agoda.com/zh-cn/pages/agoda/default/DestinationSearchResult.aspx?asq=u2qcKLxwzRU5NDuxJ0kOFxqHdHTGnNdI9yWnaEfnwQcQJD2%2FNHszlFMi2tp4vVOB8mVK8fkSAOx2ZIHnX2Ag5VIuOc5nh19nSLMOAZLcFDohboztsquKmnhn83%2FWY9toYIXLvT%2BAdK0H9U%2FBsF37%2FCF00kMrv1da9wO4Dt8pHYRttiEC19Vj5LClSDnH9ADhZ4otpQ2oE%2FLZa%2FNQm1sgB0MFzu4KwBgLvk7atJ0hdOw%3D&city=15470&tick=636202625594&pagetypeid=1&origin=CN&cid=-1&tag=&gclid=&aid=130243&userId=60f86c50-206a-47e4-93c1-e9007045a669&languageId=8&sessionId=j0qg12urhmuz0nh0oje3sjof&htmlLanguage=zh-cn&checkIn=2017-08-10&checkOut=2017-08-11&los=1&rooms=1&adults=1&children=0&priceCur=CNY&hotelReviewScore=5&ckuid=60f86c50-206a-47e4-93c1-e9007045a669'
    url = 'https://www.agoda.com/zh-cn/pages/agoda/default/DestinationSearchResult.aspx?asq=u2qcKLxwzRU5NDuxJ0kOF7mJur3qvpnR0GwXl1drX5utk8P08rki5WuYEs00ydeUpa551wZJmU1jJ1qPuvPgbHXAPleRNT%2BKzvYUA4TmMFSLtNKpqZJZndSedUWZHXXa0UoNAQnMe4%2Fv75SMDabyezhLBWlDz%2BUx1h98ixmjA6OhwNURz%2BJxVTyCno6CsS%2F%2F6maInWgV4TS9plmQWLCHvw%3D%3D&city=233&tick=636202685128&pagetypeid=103&origin=CN&cid=-1&tag=&gclid=&aid=130243&userId=60f86c50-206a-47e4-93c1-e9007045a669&languageId=8&sessionId=j0qg12urhmuz0nh0oje3sjof&htmlLanguage=zh-cn&checkIn=2017-08-10&checkOut=2017-08-11&los=1&rooms=2&adults=2&children=2&ckuid=60f86c50-206a-47e4-93c1-e9007045a669'
    pa = urlparse.urlparse(url)
    
    s = {}
    import collections
    import json
    print json.dumps(collections.OrderedDict(urlparse.parse_qsl(pa.query, keep_blank_values=1)))
#     print p.query
    for p in urlparse.parse_qsl(pa.query, keep_blank_values=1):
        print p[0], p[1]
        s[p[0]] = p[1]
#     print p.params
    print encode_url(collections.OrderedDict(urlparse.parse_qsl(pa.query, keep_blank_values=1)))


