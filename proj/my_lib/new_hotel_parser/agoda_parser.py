#! /usr/bin/env python
# coding=utf-8

import sys

import re
import requests
import execjs
from lxml import html as HTML
from util.UserAgent import GetUserAgent
# from data_obj import AgodaHotel
from proj.my_lib.models.HotelModel import AgodaHotel
from urlparse import urljoin
import json

review_num_pat = re.compile(r'(\d+)')
hotel_id_pat = re.compile(r'hotel_id=(.*?)&', re.S)
city_en_name_pat = re.compile(r'city_Name=(.*?)&', re.S)
hotel_url_pat = re.compile(r'<link rel="canonical" href="(.*?)" /><meta name="robots"', re.S)
images_url_pat = re.compile(r'images: \[(.*)],+?', re.S)

hd = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', \
      'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3', 'Connection': 'keep-alive'}

reload(sys)
sys.setdefaultencoding('utf-8')


def agoda_parser(content, url, other_info):
    hotel = AgodaHotel()
    try:
        content = content.decode('utf-8')
        root = HTML.fromstring(content)
    except:
        #print str(e)
        pass

    ph_runtime = execjs.get('PhantomJS')
    page_js = ph_runtime.compile(root.xpath('//script[contains(text(),"propertyPageParams")]/text()')[0])
    page_params = page_js.eval('propertyPageParams')
    try:
        hotel_name = page_params['hotelInfo']['name']
    except:
        try:
            hotel_name = root.xpath('//*[@id="hotelname"]/text()')[0].encode('utf-8').strip()
        except:
            try:
                hotel_name = root.xpath('//title/text()')[0].split('-')[0][:-1]
            except:
                #print str(e)
                pass

    try:
        k = hotel_name.find('(')
        # #print k
        hotel.hotel_name = hotel_name[:k if k != -1 else None]
    except:
        # #print str(e)
        hotel.hotel_name = 'NULL'
    #print 'hotel_name=>%s' % hotel.hotel_name
    # #print hotel.hotel_name

    try:
        hotel.hotel_name_en = hotel_name[k + 1 if k != -1 else None:-1 if k != -1 else None]
    except:
        hotel.hotel_name_en = 'NULL'
        # #print str(e)
    #print 'hotel.hotel_name_en=>%s' % hotel.hotel_name_en
    # #print hotel.hotel_name_en

    try:
        if page_params['hotelInfo']['address']['address'] in page_params['hotelInfo']['address']['full']:
            hotel.address = page_params['hotelInfo']['address']['full']
        else:
            hotel.address = page_params['hotelInfo']['address']['address'] + page_params['hotelInfo']['address']['full']
    except:
        hotel.address = "NULL"
    #print 'hotel.address=>%s' % hotel.address

    try:
        hotel.star = int(page_params['hotelInfo']['starRating']['icon'].split('-')[-1])
    except:
        hotel.star = -1

    if hotel.star > 5:
        if hotel.star % 5 == 0:
            hotel.star = int(hotel.star / 10)
        else:
            hotel.star = -1

    #print 'hotel.star=>%s' % hotel.star

    try:
        lat_pat = re.compile(r'latitude\" content=(.*?) \/>', re.S)
        lon_pat = re.compile(r'longitude\" content=(.*?) \/>', re.S)

        lon_text = lon_pat.findall(content)[0][1:-1]
        lat_text = lat_pat.findall(content)[0][1:-1]
        hotel.map_info = lon_text + ',' + lat_text
    except:
        # #print str(e)
        hotel.map_info = 'NULL'

    #print 'map_info=>%s' % hotel.map_info

    try:
        hotel.grade = float(page_params['reviews']['score'])
    except:
        try:
            hotel.grade = root.find_class('review-score-value')[0].text
        except:
            try:
                hotel.grade = page_params['masterRoomInfo'][0]['demographics']['grades'][0]['score']
            except:
                hotel.grade = -1
    #print 'grade=>%s' % hotel.grade

    try:
        hotel.review_num = page_params['reviews']['reviewsCount']
    except:
        try:
            review_num = root.find_class('review-based-on-section')[0].xpath('./strong/text()')[0].encode(
                'utf8').strip()
            hotel.review_num = review_num_pat.findall(review_num)[0]
        except:
            try:
                hotel.review_num = page_params['masterRoomInfo'][0]['demographics']['count']
            except:
                hotel.review_num = -1

    #print 'hotel.review_num=>%s' % hotel.review_num

    try:
        first_img = page_params.get("mosaicInitData", {}).get('images', [])[0].get('Location', 'NULL')
        first_img = urljoin('http:', first_img)
    except:
        first_img = 'NULL'

    try:
        hotel.img_items = '|'.join(filter(lambda x: 'hotel' in x,
                                          map(lambda x: 'http:' + x['Location'].split('?')[0],
                                              page_params['mosaicInitData']['images']))).encode('utf-8')
    except:
        try:
            img_lists = []
            for img in page_params['masterRoomInfo']:
                img_lists.extend(img['images'])
            hotel.img_items = '|'.join(map(lambda x: urljoin('http:', x), img_lists)).encode('utf-8')
        except:
            try:
                img_list = '|'.join(
                    [image for images in page_params['roomGridData']['masterRooms'] for image in images['images']])
                hotel.img_items = img_list
            except:
                try:
                    img_json = images_url_pat.findall(content)[0]
                    location_pat = re.compile(r'"Location":"(.*?)",', re.S)
                    img_list = location_pat.findall(img_json)
                    hotel.img_items = '|'.join(
                        map(lambda x: 'http:' + x, img_list))
                except:
                    hotel.img_items = 'NULL'
    #print 'img_items=>%s' % hotel.img_items

    try:
        hotel.hotel_url = url
    except:
        pass

    try:
        service_url = "https://www.agoda.com/api/zh-cn/Hotel/AboutHotel?hotelId={0}".format(page_params['hotelId'])
        json_data = json.loads(requests.get(service_url).content)
        hotel.service = '|'.join(
            [feature['Name'] for features in json_data['FeatureGroups'] for feature in features['Feature'] if
             feature['Available']]).encode('utf-8')

    except:
        try:
            hotel.service = '|'.join(
                [service['text'].strip() for services in page_params['featuresYouLove']['features'] for service in
                 services])
        except:
            # hotel.service = '|'.join()
            hotel.service = 'NULL'
    #print 'hotel.service=>%s' % hotel.service

    try:
        hotel.description = json_data['HotelDesc']['Overview'].strip().replace('<BR>', '').encode('utf-8')
    except:
        hotel.description = 'NULL'
    #print 'hotel.description=>%s' % hotel.description

    # hotel.check_in_time = None
    # hotel.check_in_time = None
    try:
        for checkInOut in json_data['usefulInfoGroups']:
            if '入住/退房' in checkInOut['name']:
                for item in checkInOut['items']:
                    if '入住办理起始' in item['title']:
                        hotel.check_in_time = item['description']
                        break
                for item in checkInOut['items']:
                    if '退房办理截止' in item['title']:
                        hotel.check_out_time = item['description']
                        break
                break
    except:
        pass

    if hotel.check_in_time is None and hotel.check_out_time is None:
        try:
            in_and_out = json_data.get("CheckInOutInfo", {})
            hotel.check_in_time = in_and_out.get("CheckInAndOutTime", {}).get("CheckInTime", {}).get("From", {}).get(
                "Description")
            hotel.check_out_time = in_and_out.get("CheckInAndOutTime", {}).get("CheckOutTime", {}).get("Until", {}).get(
                "Description")
        except:
            pass
    #print "hotel.check_in_time:", hotel.check_in_time
    #print "hotel.check_out_time:", hotel.check_out_time
    # 从酒店页面获取城市信息
    try:
        country_id = page_params['hotelSearchCriteria']['countryId']
        country_name = page_params['hotelInfo']['address']['countryName']
        city_name = page_params['hotelInfo']['address']['cityName']
        city_id = page_params['hotelInfo']['address']['cityId']
    except:
        country_id = 'NULL'
        country_name = 'NULL'
        city_name = 'NULL'
        city_id = 'NULL'
        #print e
        # pass

    hotel.others_info = json.dumps(
        {'country_id': country_id, 'country_name': country_name, 'city_name': city_name, 'city_id': city_id,
         'first_img': first_img, 'hid':other_info.get('hid')})
    hotel.source_city_id = city_id
    hotel.country = page_params['hotelInfo'].get('address', {}).get('countryName', '')
    hotel.city = page_params['hotelInfo'].get('address', {}).get('cityName', '')
    #print "hotel.others_info:", hotel.others_info
    #print "hotel.source_city_id:", hotel.source_city_id
    hotel.accepted_cards = 'NULL'
    #print "accepted_cards:", hotel.accepted_cards
    #print "check_in_time：", hotel.check_in_time
    #print "check_out_time:", hotel.check_out_time

    if '无线网络' in hotel.service:
        hotel.has_wifi = 'Yes'
    if '免费房内无线网络' in hotel.service:
        hotel.is_wifi_free = 'Yes'
    if 'free wi-fi' in hotel.service.lower() or 'wi-fi free' in hotel.service.lower():
        hotel.has_wifi = 'Yes'
        hotel.is_wifi_free = 'Yes'
    if '停车场' in hotel.service:
        hotel.has_parking = 'Yes'
    if '停车场免费' in hotel.service or 'parking free' in hotel.service:
        hotel.is_parking_free = 'Yes'

    #print 'hotel.has_wifi=>%s' % hotel.has_wifi
    # #print hotel.has_wifi
    #print 'hotel.is_wifi_free=>%s' % hotel.is_wifi_free
    # #print hotel.has_wifi
    #print 'hotel.has_parking=>%s' % hotel.has_parking
    # #print hotel.has_parking
    #print 'hotel.is_parking_free=>%s' % hotel.is_parking_free

    hotel.source = 'agoda'
    hotel.hotel_url = url.encode('utf-8')
    if other_info.get('hid'):
        hotel.source_id = re.search('hotelId: ?(\d+),', content).groups()[0]
        # hotel.source_id = re.search('cityId: ?(\d+),', content).groups()[0]
    else:
        hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    # others_info_dict = hotel.__dict__
    # hotel.others_info = json.dumps(others_info_dict)
    # #print hotel

    return hotel


if __name__ == '__main__':
    from util.UserAgent import GetUserAgent
    from common.common import get_proxy

    headers = {
        'User-agent': GetUserAgent(),
        "authority": "www.agoda.com"
    }

    other_info = {
        'source_id': '1006311',
        'city_id': '11164',
        'hid': 100
    }
    # url = 'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_agoda&id=329cf4fa7c9196ce026aa1053c652c2f'
    # url = 'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_agoda&id=49536fe85753dfd12ea88d0700bda26d'
    # url = 'https://www.agoda.com/zh-cn/wingate-by-wyndham-arlington_2/hotel/all/arlington-tx-us.html?checkin=2017-08-03&los=1&adults=1&rooms=1&cid=-1&searchrequestid=09d590d3-cc17-4046-89a1-112b6ed35266'
    # url = 'https://www.agoda.com/zh-cn/hotel-las-bovedas/hotel/badajoz-es.html?checkin=2017-12-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=65bc1980-4fcf-4ed1-bdf0-438a11704f7a'
    # url = 'https://www.agoda.com/zh-cn/estudio-casco-antiguo/hotel/all/badajoz-es.html?checkin=2017-12-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=65bc1980-4fcf-4ed1-bdf0-438a11704f7'
    # url = 'https://www.agoda.com/zh-cn/ilunion-golf-badajoz-hotel/hotel/badajoz-es.html?checkin=2017-12-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=65bc1980-4fcf-4ed1-bdf0-438a11704f7a'
    # url = 'https://www.agoda.com/zh-cn/hotel-lisboa/hotel/all/badajoz-es.html?checkin=2017-12-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=65bc1980-4fcf-4ed1-bdf0-438a11704f7a'
    url = 'https://www.agoda.com/zh-cn/oarsman-s-bay-lodge/hotel/yasawa-islands-fj.html?checkin=2017-11-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=b5bd9776-41c6-4fdd-b361-4abcaf8c8703'
    # url = 'https://www.agoda.com/zh-cn/hotel-huatian-chinagora/hotel/alfortville-fr.html?checkin=2017-12-20&los=1&adults=2&rooms=1&cid=-1&searchrequestid=f53c35ca-007e-4974-af8f-ebfa20c4dfee'
    # url = 'https://www.agoda.com/zh-cn/puesta-del-sol-apartment/hotel/all/asilah-ma.html?checkin=2017-12-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=a00c61b5-db95-40f9-b5c3-a385219f7e7a'
    # url = 'https://www.agoda.com/zh-cn/ana-o-tai/hotel/all/hanga-roa-cl.html?checkin=2017-12-15&los=1&adults=2&rooms=1&cid=-1&searchrequestid=1b174d8d-2aef-4fea-836d-fb7a5e70e234'
    # url = 'https://www.agoda.com/zh-cn/cabanas-teo/hotel/all/isla-de-pascua-cl.html?checkin=2017-12-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=5460efbf-de01-4b89-99c8-11e1adc2f066'
    url = 's23'
    # url = 'https://www.agoda.com/zh-cn/hare-vivanka/hotel/all/hanga-roa-cl.html?checkin=2017-12-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=60408400-065d-49f8-8965-d45ef26b7d91'
    # url = 'https://www.agoda.com/zh-cn/cabana-meme/hotel/all/hanga-roa-cl.html?checkin=2017-12-25&los=1&adults=2&rooms=1&cid=-1&searchrequestid=60408400-065d-49f8-8965-d45ef26b7d91'
    # url = 'https://www.agoda.com/zh-cn/hotel-alagare/hotel/lausanne-ch.html?checkin=2017-12-07&los=1&adults=2&rooms=1&cid=-1&searchrequestid=9127dc90-fd5e-4cbb-aa22-4cf62afbdecd'
    # url = 'https://www.agoda.com/zh-cn/grand-hyatt-new-york-hotel/hotel/new-york-ny-us.html?checkin=2017-12-20&los=1&adults=2&rooms=1&cid=-1&searchrequestid=7e5812dd-d6a4-4ca3-90a1-60437e475f93'
    url = 'https://www.agoda.com/zh-cn/hotel-the-celestine-tokyo-shiba/hotel/tokyo-jp.html?checkin=2017-12-17&los=1&adults=3&rooms=1&searchrequestid=b0293d9f-56be-46ad-998e-3a14b8601594&isMRS=1'
    url = 'https://www.agoda.com/zh-cn/royal-park-hotel-the-shiodome-tokyo/hotel/tokyo-jp.html?checkin=2017-12-17&los=1&adults=3&rooms=1&searchrequestid=35cdc5b6-2e05-4924-b71e-479692ddb593&isMRS=1'
    url = 'https://www.agoda.com/zh-cn/conrad-macao-cotai-central/hotel/macau-mo.html?checkin=2017-12-17&los=1&adults=3&rooms=1&searchrequestid=5bd92238-b4f5-4d41-a958-051575b96f71&dodhotel=1&isMRS=0'
    url = 'https://www.agoda.com/zh-cn/kakkos-beach-hotel-adults-only/hotel/crete-island-gr.html?selectedproperty=4619813&checkIn=2018-04-29&los=1&rooms=1&adults=2&childs=0&cid=1590325&tag=hid4619813%2cpidWtiG9MCoCx4AAK-P--YAAAAY'
    url = 'https://www.agoda.com/zh-cn/hotel-gri-mar/hotel/llansa-es.html?selectedproperty=229354&checkIn=2018-04-29&los=1&rooms=1&adults=2&childs=0&cid=1590325&tag=hid229354%2cpidWthg9H8AAAEAAK5YRRQAAAAe'
    page = requests.get(url=url, headers=headers)
    page.encoding = 'utf8'
    content = page.text

    result = agoda_parser(content, url, other_info)
