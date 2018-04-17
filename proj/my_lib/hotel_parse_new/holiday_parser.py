#coding:utf-8
import requests
import sys
import re
import json
from lxml.html import fromstring
from lxml import etree
# from mioji.common.utils import setdefaultencoding_utf8
from proj.my_lib.models.HotelModel import HotelNewBase
# from mioji.common.class_common import Hotel_New as HotelNewBase
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
    hotel.review_num = resp.get('profile', '').get('totalReviews', '')
    hotel.check_in_time = resp.get('policies', '').get('checkinTime', '')
    hotel.check_out_time = resp.get('policies', '').get('checkoutTime', '')
    first_img = resp.get('profile', '')
    if first_img:
        first_img = first_img.get('primaryImageUrl', '')
        if first_img:
            first_img = first_img.get('originalUrl', '')
            hotel.Img_first = first_img
    hotel.description = resp.get('profile', '').get('longDescription', '') + '\n' + resp.get('profile', '').get('shortDescription', '')
    # detail['has_wifi'] = 'Yes' if any([u'无线互联网' in ''.join(i.values()) or 'wifi' in ''.join(i.values()) for i in
    #                                         resp.get('facilities', '')]) else detail.get('has_wifi', 'Null')
    # detail['service'] = detail.get('service', '') + get_api_server(resp)
    facilities_dict = {'Swimming_Pool': '泳池', 'gym': '健身', 'SPA': 'SPA', 'Bar': '酒吧', 'Coffee_house': '咖啡厅',
                       'Tennis_court': '网球场', 'Golf_Course': '高尔夫球场', 'Sauna': '桑拿', 'Mandara_Spa': '水疗中心',
                       'Recreation': '儿童娱乐场', 'Business_Centre': '商务中心', 'Lounge': '行政酒廊',
                       'Wedding_hall': '婚礼礼堂', 'Restaurant': '餐厅', 'Parking': '停车',
                       'Airport_bus': '机场班车', 'Valet_Parking': '代客泊车', 'Call_service': '叫车服务',
                       'Rental_service': '租车服务', 'Room_wifi': '无线互联网', 'Room_wired': '有线互联网', 'Public_wifi': '无线互联网', 'Public_wired': '有线互联网'}
    reverse_facility_dict = {v: k for k, v in facilities_dict.items()}
    service_dict = {'Luggage_Deposit': '行李寄存', 'front_desk': '24小时前台', 'Lobby_Manager': '24小时大堂经理',
                    '24Check_in': '24小时办理入住', 'Security': '24小时安保', 'Protocol': '礼宾服务',
                    'wake': '叫醒服务', 'Chinese_front': '中文前台', 'Postal_Service': '邮政服务',
                    'Fax_copy': '传真/复印', 'Laundry': '洗衣服务', 'polish_shoes': '擦鞋服务', 'Frontdesk_safe': '保险',
                    'fast_checkin': '快速办理入住', 'ATM': '自动柜员机(ATM)/银行服务', 'child_care': '儿童看护',
                    'Food_delivery': '送餐服务'}
    reverse_sevice_dict = {v: k for k, v in service_dict.items()}
    facilities = resp.get("facilities", "")
    for each in facilities:
        if each['id'] == 'NO_PETS_ALLOWED' or each['id'] == 'PETS_ALLOWED':
            hotel.pet_type = each['name']
        for fac_value in facilities_dict.values():
            if fac_value in each['name']:
                hotel.facility_content[reverse_facility_dict[fac_value]] = each['name']
        for ser_value in service_dict.values():
            if ser_value in each['name']:
                hotel.service_content[reverse_sevice_dict[ser_value]] = each['name']
    fea_str = get_api_server(resp)
    tree = etree.HTML(content2)
    ser_str = get_ota_server(tree, '上网', '互联网', '泳', '退房', '餐', '预定', '停车', '健身', '运动', '泳池', '特色', '服务')
    hotel_services_info = fea_str + ser_str
    hotel.others_info = json.dumps({
        'city': detail.get('city', ''),
        'country': detail.get('country', ''),
        'first_img': first_img,
        'source_city_id': other_info.get('source_city_id', ''),
        'hotel_services_info': hotel_services_info
    })
    hotel.img_items = get_all_pics(tree)

    # content_list = tree.xpath("//div[@class='accordian-content']/li/div[@class='header']/h2/span/text()")
    # index = 1
    # for content in content_list:
    #     if content == "停车":
    #         parking_list = tree.xpath("//div[@class='accordian-content']/li[{}]/div[@class='item-content']/ul/li/text()".format(index))
    #         hotel.facility_content['Parking'] = " ".join(parking_list)
    #     if content == "宠物政策":
    #         pet_list = tree.xpath("//div[@class='accordian-content']/li[{}]/div[@class='item-content']/ul/li/text()".format(index))
    #         hotel.pet_type = " ".join(pet_list)
    #     index += 1
    hotel.hotel_zip_code = hotel.postal_code
    # try:
    #     hotel.hotel_phone = tree.xpath("//div[@class='resdirect-num tel-no']/span/a/text()")[0]
    # except Exception as e:
    #     hotel.hotel_phone = "NULL"
    res = hotel.to_dict()
    # res = json.loads(res)
    # print json.dumps(res, ensure_ascii=False)
    return res


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
    for i in resp.get('contact', ''):
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
    # url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/epatx/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/EPATX/details'
    # url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/gsomm/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/GSOMM/details'
    # url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/cofks/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/COFKS/details'
    # url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/jnljo/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/JNLJO/details'
    # url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/nlees/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/NLEES/details'
    url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/aadal/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/AADAL/details'
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
    print result

