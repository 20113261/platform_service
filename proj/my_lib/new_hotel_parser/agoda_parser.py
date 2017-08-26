#! /usr/bin/env python
# coding=utf-8

import sys

import re
import requests
import execjs
from lxml import html as HTML
from util.UserAgent import GetUserAgent
from data_obj import AgodaHotel, DBSession

# pattern
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
    except Exception as e:
        print str(e)

    ph_runtime = execjs.get('PhantomJS')
    page_js = ph_runtime.compile(root.xpath('//script[contains(text(),"propertyPageParams")]/text()')[0])
    page_params = page_js.eval('propertyPageParams')

    try:
        hotel_name = page_params['hotelInfo']['name']
    except:
        try:
            hotel_name = root.xpath('//*[@id="hotelname"]/text()')[0].encode('utf-8').strip()
        except Exception, e:
            try:
                hotel_name = root.xpath('//title/text()')[0].split('-')[0][:-1]
            except Exception, e:
                print str(e)

    try:
        k = hotel_name.find('(')
        # print k
        hotel.hotel_name = hotel_name[:k if k != -1 else None]
    except Exception, e:
        # print str(e)
        hotel.hotel_name = 'NULL'
    print 'hotel_name=>%s' % hotel.hotel_name
    # print hotel.hotel_name

    try:
        hotel.hotel_name_en = hotel_name[k + 1 if k != -1 else None:-1 if k != -1 else None]
    except Exception, e:
        hotel.hotel_name_en = 'NULL'
        # print str(e)
    print 'hotel.hotel_name_en=>%s' % hotel.hotel_name_en
    # print hotel.hotel_name_en

    try:
        hotel.address = page_params['hotelInfo']['address']['full']
    except:
        hotel.address = "NULL"
    print 'hotel.address=>%s' % hotel.address
    # print hotel.address

    try:
        hotel.star = int(page_params['hotelInfo']['starRating']['icon'].split('-')[-1])
    except:
        hotel.star = -1

    if hotel.star > 5:
        if hotel.star % 5 == 0:
            hotel.star = int(hotel.star / 10)
        else:
            hotel.star = -1

    print 'hotel.star=>%s' % hotel.star

    try:
        lat_pat = re.compile(r'latitude\" content=(.*?) \/>', re.S)
        lon_pat = re.compile(r'longitude\" content=(.*?) \/>', re.S)

        lon_text = lon_pat.findall(content)[0][1:-1]
        lat_text = lat_pat.findall(content)[0][1:-1]
        hotel.map_info = lon_text + ',' + lat_text
    except Exception, e:
        # print str(e)
        hotel.map_info = 'NULL'

    print 'map_info=>%s' % hotel.map_info
    # print hotel.map_info
    try:
        hotel.grade = float(page_params['reviews']['score'])
    except:
        try:
            hotel.grade = root.find_class('review-score-value')[0].text
        except:
            hotel.grade = -1
    print 'grade=>%s' % hotel.grade
    # print hotel.grade
    try:
        hotel.review_num = page_params['reviews']['reviewsCount']
    except:
        try:
            review_num = root.find_class('review-based-on-section')[0].xpath('./strong/text()')[0].encode(
                'utf8').strip()
            hotel.review_num = review_num_pat.findall(review_num)[0]
        except:
            hotel.review_num = -1

    print 'hotel.review_num=>%s' % hotel.review_num
    # print hotel.review_num

    try:
        hotel.img_items = '|'.join(filter(lambda x: 'hotelImages' in x,
                                          map(lambda x: 'http:' + x['Location'].split('?')[0],
                                              page_params['mosaicInitData']['images'])))
    except:
        try:
            # hotel.img_items = '|'.join(
            #     map(lambda x: 'http:' + x, root.get_element_by_id('hotel-gallery').xpath('./div/img/@src')))
            img_json = images_url_pat.findall(content)[0]
            location_pat = re.compile(r'"Location":"(.*?)",', re.S)
            img_list = location_pat.findall(img_json)
            hotel.img_items = '|'.join(
                map(lambda x: 'http:' + x, img_list))
        except:
            hotel.img_items = 'NULL'

    print 'img_items=>%s' % hotel.img_items
    # print hotel.img_items

    try:
        hotel.hotel_url = url
    except:
        pass

    try:
        headers = {
            'User-agent': GetUserAgent()
        }
        url_about = 'https://www.agoda.com/NewSite/zh-cn/Hotel/AboutHotel?hotelId={0}&languageId=8&hasBcomChildPolicy=False'.format(
            other_info['source_id'])
        page_about = requests.get(url=url_about, headers=headers)
        page_about.encoding = 'utf8'
        about_content = page_about.text

        about_root = HTML.fromstring(about_content)
    except Exception, e:
        about_root = HTML.fromstring('')

    try:
        hotel.description = ''.join(about_root.xpath('//div[@data-selenium="abouthotel-detail"]/text()')).encode(
            'utf8').strip()
    except:
        hotel.description = 'NULL'
    print 'hotel.description=>%s' % hotel.description

    try:
        hotel.service = '|'.join(about_root.xpath('//span[@data-selenium="available-feature"]/text()')).encode(
            'utf8').strip()
    except:
        hotel.service = 'NULL'
    print 'hotel.service=>%s' % hotel.service

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

    print 'hotel.has_wifi=>%s' % hotel.has_wifi
    # print hotel.has_wifi
    print 'hotel.is_wifi_free=>%s' % hotel.is_wifi_free
    # print hotel.has_wifi
    print 'hotel.has_parking=>%s' % hotel.has_parking
    # print hotel.has_parking
    print 'hotel.is_parking_free=>%s' % hotel.is_parking_free

    hotel.source = 'agoda'
    hotel.hotel_url = url.encode('utf-8')
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    from util.UserAgent import GetUserAgent
    from common.common import get_proxy

    # PROXY = get_proxy(source="Platform")
    # proxies = {
    #     'http': 'socks5://' + PROXY,
    #     'https': 'socks5://' + PROXY
    # }
    headers = {
        'User-agent': GetUserAgent(),
        "authority": "www.agoda.com"
    }
    # url = 'http://www.agoda.com/city-backpacker-biber/hotel/all/zurich-ch.html?checkin=2016-12-28&los=1&adults=1&rooms=1&cid=-1&searchrequestid=b31690e6-b5b6-4fb2-a924-b1daa147e9ae'
    # url = 'https://www.agoda.com/zh-cn/tropical-palms-elite-two-bedroom-cottage-104/hotel/all/orlando-fl-us.html?checkin=2017-08-03&los=1&adults=1&rooms=1&cid=-1&searchrequestid=3083d8d6-bbfe-45fd-a47c-2e5aa50b99a2'
    # url = 'https://www.agoda.com/zh-cn/tropical-palms-elite-two-bedroom-cottage-104/hotel/all/orlando-fl-us.html?checkin=2017-08-03&los=1&adults=1&rooms=1&cid=-1&searchrequestid=3083d8d6-bbfe-45fd-a47c-2e5aa50b99a2'
    # url = 'https://www.agoda.com/zh-cn/tropical-palms-elite-two-bedroom-cottage-104/hotel/orlando-fl-us.html?asq=AbQz%2FJFl%2FcBA96vs5%2Fi%2FsKR3foYRS4x3%2F4l3z6pYa26QxEZ3vNxq0q36TUBn%2BpiKKVwQksJRNjhBbE6hOoyfwo4hZxgFVEtNaFLVyhOu6FnvZdIRAOWrnOYDO7qzRDkDXiyX8%2F8HJ3jSDjfHoaOyVQO0w7eSm%2B7cRtAD45wellgsMqeQTY%2FB1d0%2FmNL8J%2FOjkqBRDmLeOBeebtAGQt1SQjGopgB0OGhZuTdGK4p8iOg%3D&hotel=1705901&tick=636301764578&pagetypeid=7&origin=CN&cid=-1&tag=&gclid=&aid=130243&userId=eda0f3f0-783f-4202-8592-5e7f3ec626fd&languageId=8&sessionId=rsci0zuyujepom000loqtfso&storefrontId=3&currencyCode=CNY&htmlLanguage=zh-cn&trafficType=User&cultureInfoName=zh-CN&checkIn=2017-10-04&checkout=2017-10-05&los=1&rooms=1&adults=1&childs=0&ckuid=eda0f3f0-783f-4202-8592-5e7f3ec626fd'
    # url = 'http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705137.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021112240039787526.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021112240039787533.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705131.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705122.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705124.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021111170039786134.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021111170039786135.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705103.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705119.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705120.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021111170039786138.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705133.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021112240039787527.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021112240039787528.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_14082915180021705098.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021112240039787529.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021112240039787530.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021112240039787531.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16021112240039787532.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16030809190040534728.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16030809190040534729.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16030809250040536675.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16030809250040536674.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16030809180040534719.jpg?s=1024x768|http://pix6.agoda.net/hotelImages/148/148964/148964_16030809180040534720.jpg?s=1024x768'
    # url = 'https://www.agoda.com/zh-cn/hotel-piena-kobe/hotel/kobe-jp.html'
    # url = 'https://www.agoda.com/zh-cn/marriott-hotel-downtown-abu-dhabi/hotel/abu-dhabi-ae.html'
    # if 'www.agoda.com/zh-cn' not in url:
    #     url = url.replace('www.agoda.com', 'www.agoda.com/zh-cn')

    other_info = {
        'source_id': '1006311',
        'city_id': '11164'
    }
    # url = 'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_agoda&id=329cf4fa7c9196ce026aa1053c652c2f'
    # url = 'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_agoda&id=49536fe85753dfd12ea88d0700bda26d'
    # url = 'https://www.agoda.com/zh-cn/wingate-by-wyndham-arlington_2/hotel/all/arlington-tx-us.html?checkin=2017-08-03&los=1&adults=1&rooms=1&cid=-1&searchrequestid=09d590d3-cc17-4046-89a1-112b6ed35266'
    url = 'http://www.agoda.com/criterion-pub-kitchen/hotel/newcastle-au.html?checkin=2016-11-22&los=1&adults=1&rooms=1&cid=-1&searchrequestid=8165bd8e-72e9-452a-a3c7-4ea693b1cee3'
    page = requests.get(url=url, headers=headers)
    page.encoding = 'utf8'
    content = page.text
    # content = open('/tmp/abfc3512-1119-4e89-841b-55b88fd821ff_0.html').read()

    result = agoda_parser(content, url, other_info)
    # try:
    #     session = DBSession()
    #     session.add(result)
    #     session.commit()
    #     session.close()
    # except Exception as e:
    #     print str(e)
