#coding:utf-8
import requests
import re
import json
from lxml.html import fromstring
from mioji.common.utils import setdefaultencoding_utf8
from proj.my_lib.models.HotelModel import HotelBase
setdefaultencoding_utf8()
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
    hotel = HotelBase()
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
    re_match = re.search('/hotels/cn/zh/(\w+)/hoteldetail', url)
    hotel_code = re_match.group(1) if re_match else ''


    resp = json.loads(content1)['hotelInfo']
    detail['hotel_url'] = url
    detail['hotel_name'] = resp.get('profile', '').get('name', '')
    detail['hotel_name_en'] = detail.get('hotel_name_en', '')
    detail['source'] = 'holiday'
    detail['source_id'] = other_info.get('source_id', '') or hotel_code
    detail['source_city_id'] = other_info.get('source_city_id', '')
    detail['brand_name'] = resp.get('brandInfo', '').get('brandName', '')
    detail['map_info'] = str(resp.get('profile', '').get('latitude', '')) + ',' + str(resp.get('profile', '').get('longitude', ''))
    detail['address'] = get_all_street(resp)
    detail['city'] = resp.get('address', '').get('city', '')
    detail['country'] = resp.get('address', '').get('country', '').get('name', '')
    detail['city_id'] = other_info.get('city_id', '')
    detail['postal_code'] = resp.get('address', '').get('zip', '')
    detail['star'] = '-1'
    detail['grade'] = resp.get('profile', '').get('averageReview', '')
    detail['review_num'] = resp.get('profile', '').get('totalReviews', '')
    detail['check_in_time'] = resp.get('policies', '').get('checkinTime', '')
    detail['check_out_time'] = resp.get('policies', '').get('checkoutTime', '')
    first_img = resp.get('profile', '')
    if first_img:
        first_img = first_img.get('primaryImageUrl', '')
        if first_img:
            first_img = first_img.get('originalUrl', '')
    detail['others_info'] = json.dumps({
        'city': detail.get('city', ''),
        'country': detail.get('country', ''),
        'first_img': first_img,
        'source_city_id': other_info.get('source_city_id', '')
    })
    detail['description'] = resp.get('profile', '').get('longDescription', '') + '\n' + resp.get('profile', '').get('shortDescription', '')
    detail['has_wifi'] = 'Yes' if any([u'无线互联网' in ''.join(i.values()) or 'wifi' in ''.join(i.values()) for i in
                                            resp.get('facilities', '')]) else detail.get('has_wifi', 'Null')
    detail['service'] = detail.get('service', '') + get_api_server(resp)

    tree = fromstring(content2)
    detail['is_wifi_free'] = judge_xxx_available(tree, '上网', 'wifi', '无线')
    detail['has_wifi'] = 'Yes' if detail['is_wifi_free'] == 'Yes' or detail[
        'is_wifi_free'] == 'No' else detail.get('has_wifi', 'Null')
    detail['is_parking_free'] = judge_xxx_available(tree, '停车', '车场')
    detail['has_parking'] = 'Null' if detail.get('is_parking_free', '') == 'Null' else 'Yes'
    detail['img_items'] = get_all_pics(tree)
    detail['service'] = detail.get('service', '') + get_ota_server(tree, '上网', '互联网', '泳', '退房', '餐', '预定',
                                                                   '停车', '健身', '运动', '泳池', '特色', '服务')
    for k, v in detail.items():
        setattr(hotel, k, v)
    return hotel


def get_all_street(resp):
    country = resp.get('address', '').get('country', '').get('name', '')
    street = ''
    for k, v in resp.get('address', '').items():
        if k.startswith('street') and v:
            street += v
    return country + street


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
    service = '|酒店特色：'
    service += ', '.join([i['name'] for i in resp.get('badges') if i.get('name')]).lstrip().rstrip() + '|' + '酒店设施：'
    service += ', '.join([i['name'] for i in resp.get('facilities') if i.get('name')]).lstrip().rstrip() + '|' + '联系方式：'
    for i in resp['contact']:
        service += '，'.join([k + ':' + v for k, v in i.items() if v]).lstrip().rstrip() + '|'
    service += '酒店可以使用{}'.format(''.join(i['name'] for i in resp['policies'].get('acceptedCurrencies') if i.get('name')).lstrip().rstrip())
    return service + '|'


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
    return '|' + '|'.join(service)


if __name__ == '__main__':
    url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/empcd/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/EMPCD/details'
    url2, url1 = url.split('#####')
    # url1 = 'https://apis.ihg.com/hotels/v1/profiles/EMPCD/details'
    # url2 = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/empcd/hoteldetail'
    print 'start 1'
    content1 = requests.get(url1, headers={'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y', 'ihg-language': 'zh-CN'}).text
    print 'got 1'
    content2 = requests.get(url2, headers={
                        'accept': 'application/json, text/plain, */*',
                        'Content-Type': 'application/json; charset=UTF-8',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        'ihg-language': 'zh-CN',
                    }).text
    print 'start 2'
    print 'got 2'
    # content3可选，用来抓英文名
    print 'start 3'
    content3 = requests.get(url1, headers={'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y'}).text
    print 'got 3'
    result = holiday_parser((content1, content2, content3), url2, {})
    print '\n'.join(['%s:%s' % item for item in result.__dict__.items()])

