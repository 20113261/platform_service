#coding:utf-8
import requests
import sys
import re
import json
from lxml.html import fromstring
from lxml import etree
# from mioji.common.utils import setdefaultencoding_utf8
from proj.my_lib.models.HotelModel import HotelNewBase
#from mioji.common.class_common import Hotel_New as HotelNewBase
reload(sys)
sys.setdefaultencoding('utf-8')
# setdefaultencoding_utf8()
# class HotelBase(object):
#     __asd__ = 'asdasd'
#     a = '1111'


def holiday_parser(content, url, other_info):
    """
    酒店详情的爬虫
    :param content: 包含3个或2个content的元组，分别为json和xml和json格式，其中第三个json可选，主要用来抓酒店的英文名
    :param url: 酒店详情页的url
    :param other_info: 包含city_id, source_id 的字典
    :return: 返回一个HotelBase的实例
    """
    hotel = HotelNewBase()
    detail = {}
    if len(content) == 3:
        content1, content2, content3 = content
        try:
            en_json = json.loads(content3)
            detail['hotel_name_en'] = en_json['hotelInfo']['profile']['name']
        except:
            pass
    else:
        content1, content2 = content
    tree = etree.HTML(content2)
    re_match = re.search('/hotels/cn/zh/(\w+)/hoteldetail', url)
    hotel_code = re_match.group(1) if re_match else ''

    # with open('igh.html', 'w') as f:
    #     f.write(content2)
    resp = json.loads(content1)['hotelInfo']
    hotel.hotel_url = url
    hotel.hotel_name = resp.get('profile', '').get('name', '')
    hotel.hotel_name_en = detail.get('hotel_name_en', '')
    hotel.source = 'holiday'
    hotel.source_id = other_info.get('source_id', '') or hotel_code
    # hotel.source_city_id = other_info.get('source_city_id', '')
    hotel.brand_name = resp.get('brandInfo', '').get('brandName', '')
    hotel.map_info = str(resp.get('profile', '').get('longitude', '')) + ',' + str(resp.get('profile', '').get('latitude', ''))
    hotel.address = get_all_street(resp)
    hotel.city = resp.get('address', '').get('city', '')
    hotel.country = resp.get('address', '').get('country', '').get('name', '')
    hotel.city_id = other_info.get('city_id', '')
    hotel.postal_code = resp.get('address', '').get('zip', '')
    hotel.star = '-1'
    hotel.grade = resp.get('profile', '').get('averageReview', '')
    if not hotel.grade:
        hotel.grade = "".join(tree.xpath('//*[@id="review-link"]/span[@itemprop="ratingValue"]/text()'))
    hotel.review_num = resp.get('profile', '').get('totalReviews', '')
    if not hotel.review_num:
        hotel.review_num = ''.join(tree.xpath('//*[@id="review-link"]/span/span[@itemprop="reviewCount"]/text()'))
    hotel.check_in_time = resp.get('policies', '').get('checkinTime', '')
    hotel.check_out_time = resp.get('policies', '').get('checkoutTime', '')
    first_img = resp.get('profile', '')
    if first_img:
        first_img = first_img.get('primaryImageUrl', '')
        if first_img:
            first_img = first_img.get('originalUrl', '')
            hotel.Img_first = first_img
    description = resp.get('profile', '').get('longDescription', '')
    hotel.description = re.sub('<.*?>','',description)


    fea_str = get_api_server(resp)

    hotel_services_info = fea_str
    hotel.others_info = json.dumps({
        'city': detail.get('city', ''),
        'country': detail.get('country', ''),
        'first_img': first_img,
        'source_city_id': other_info.get('source_city_id', ''),
        'hotel_services_info': hotel_services_info
    })
    hotel.img_items = get_all_pics(tree)

    hotel.hotel_zip_code = hotel.postal_code
    res = hotel.to_dict()
    return res


def get_all_street(resp):
    address = []
    country = resp.get('address', {}).get('country', {}).get('name', '')
    city =  resp.get('address', {}).get("city","")
    zip = resp.get('address', {}).get("zip", "")
    state = resp.get('address', {}).get('state', {}).get("name","")
    street = ''
    for k, v in resp.get('address', '').items():
        if k.startswith('street') and v:
            street += v + ' '
    if street:
        address.append(street)
    if city:
        address.append(city)
    if state:
        address.append(state)
    if zip:
        address.append(zip)
    if country:
        address.append(country)
    return ' '.join([street, city, state, zip, country])


def get_all_pics(tree):
    all_pics = tree.xpath("//img[@data-medium-desktop]/@data-desktop")
    distinct = list(set([i.split('?', 1)[0] for i in all_pics if '?' in i]))
    return '|'.join(['http:' + i for i in distinct])


def judge_xxx_available(tree, *args):
    """
    这里逻辑爆炸，我的逻辑是，没找到相关元素返回Null，否则返回Yes，No
    """
    all_nodes = []
    for i in args:
        related_ele = [j for j in tree.xpath(u'//*[contains(text(), "{}")]'.format(i))] + [j for j in tree.xpath(u'//*[contains(text(), "{}")]/following-sibling::*'.format(i))]
        for _ in related_ele:
            child = _.getchildren()
            if child:
                related_ele += child
                related_ele = list(set(related_ele))
        all_nodes += [i.text for i in related_ele if isinstance(i.text, unicode) or isinstance(i.text, str)]
    if not all_nodes:
        return 'Null'
    text = ''.join(all_nodes)
    return 'Yes' if '免费' in text and '不提供免费' not in text and '不免费' not in text and '收费' not in text else 'No' and any(i in text for i in args)


def get_api_server(resp):
    service = "|".join([i["name"] for i in resp.get('facilities') if i.get('name')]).lstrip().rstrip()
    badges = "|".join([i["name"] for i in resp.get('badges') if i.get('name')]).lstrip().rstrip()
    return service + '|'+badges


def get_ota_server(tree, *args):
    service = []
    for i in args:
        related_ele = [j for j in tree.xpath(u'//*[contains(text(), "{}")]/following-sibling::*'.format(i))] + [j for j in tree.xpath(u'//*[contains(text(), "{}")]'.format(i))]
        for _ in related_ele:
            child = _.getchildren()
            if child:
                related_ele += child
        related_ele = list(set(related_ele))
        all_text = [k for k in [t.text.lstrip().rstrip() for t in related_ele if t.text] if
                    5 < len(k) < 200 and re.search(ur"[\u4e00-\u9fa5]+", k) and k]
        if not all_text:
            continue
        text = max(all_text, key=len) if all_text else ''
        if text not in service:
            service.append(text)
    return '|'.join(service)


if __name__ == '__main__':

    url_s = [
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/epatx/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/EPATX/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/gsomm/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/GSOMM/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/cofks/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/COFKS/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/jnljo/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/JNLJO/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/nlees/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/NLEES/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/aadal/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/AADAL/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/abelv/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/ABELV/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/abqtw/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/ABQTW/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/abzcc/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/ABZCC/details',
    'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/adlah/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/ADLAH/details']
    for url in url_s:
        url2, url1 = url.split('#####')
        # url1 = 'https://apis.ihg.com/hotels/v1/profiles/EMPCD/details'
        # url2 = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/empcd/hoteldetail'
        print 'start 1'
        content1 = requests.get(url1, headers={'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y', 'ihg-language': 'zh-CN',
                                               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}).text
        print 'got 1'
        content2 = requests.get(url2, headers={
                            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                            # 'Content-Type': 'application/json; charset=UTF-8',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
                            # 'ihg-language': 'zh-CN',
                            'cache-control': "max-age=0",
                            # 'Postman-Token': "f7e3b40e-12cf-c7e7-f0a7-d729ea761727"
                        }).text
        print 'start 2'
        print 'got 2'
        # content3可选，用来抓英文名
        print 'start 3'
        content3 = requests.get(url1, headers={'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                                               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
                                               }).text
        print 'got 3'
        # other_info = {
        #     'source_city_id': '10000',
        #
        # }
        result = holiday_parser((content1, content2, content3), url2, {})
        # print '\n'.join(['%s:%s' % item for item in result.__dict__.items()])
        # res = json.loads(result)
        with open("holiday.json",'a') as w:
            w.write(result+'\n')
        print result

