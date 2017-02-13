# coding=utf-8
"""
    @author:HouRong
    @description:
    一些关于酒店详细信息的函数
"""
import logging

from suds.client import Client

import database as db

logging.basicConfig(level=logging.ERROR)


def get_client(url, auth):
    """
    获取 webservice client
    :param url: 对方接口 url
    :param auth: 验证信息字典
    :return: suds client
    """
    client = Client(url)
    h = client.factory.create('ns2:AuthenticationHeader')
    for k, v in auth.items():
        h[k] = v
    client.set_options(soapheaders=h)
    return client


def queryGetHotelDetailsV3(h_ids):
    """
    通过对方的 API ,查询 Hotel 信息
    :param h_ids:对方的 hotel_id
    :return: suds 对象, hotel
    """
    url = 'http://thfwsv3.touricoholidays.com/HotelFlow.svc?wsdl'
    auth = dict(LoginName='MIO106', Password='@2NzbzDU', Culture='zh_CN', Version='7.123')
    client = get_client(url, auth)
    features = client.factory.create('ns7:ArrayOfFeature')
    hotel_ids = client.factory.create('ns7:ArrayOfHotelID')
    items = []
    for h_id in h_ids:
        hotel_id = client.factory.create('ns7:HotelID')
        hotel_id._id = str(h_id)
        items.append(hotel_id)
    hotel_ids.HotelID = items
    res = client.service.GetHotelDetailsV3(hotel_ids, features)
    return res.TWS_HotelDetailsV3.Hotel


def get_per_data(hotel, city_id):
    """
    获取 Hotel 的详细信息
    :param hotel: suds 的 hotel 对象
    :param city_id: 城市 id
    :return: hotel 信息 tuple
    """
    try:
        hotel_name = hotel._name
        hotel_name_en = hotel._name
        source = 'touricoholidays'
        source_id = hotel._hotelID
    except:
        return None

    try:
        brand_name = hotel._brand
    except:
        brand_name = ''
    map_info = '{0},{1}'.format(hotel.Location._longitude, hotel.Location._latitude)
    try:
        address = hotel.Location._address
    except:
        address = ''
    try:
        city = hotel.Location._city
    except:
        city = ''
    try:
        country = hotel.Location._country
    except:
        country = ''
    try:
        star = hotel._starLevel
    except:
        star = ''

    service = []
    try:
        for amenity in hotel.Amenities[0]:
            service.append(amenity._name)
    except:
        pass

    try:
        for facility in hotel.RoomType[0].Facilities[0]:
            service.append(facility._name)
    except:
        pass
    service = '|'.join(service)

    img_items = []
    try:
        for img in hotel.Media[0][0]:
            img_items.append(img._path)
    except:
        pass
    img_items = '|'.join(img_items)

    description = []
    try:
        for desc in hotel.Descriptions.LongDescription.Description:
            description.append(desc._value)
    except:
        try:
            description.append(
                (hotel.Descriptions.LongDescription.FreeTextLongDescription).replace('\n', '').replace(' ', ''))
        except:
            pass
    description = ' '.join(description)
    try:
        check_in_time = hotel._checkInTime
    except:
        check_in_time = ''
    try:
        check_out_time = hotel._checkOutTime
    except:
        check_out_time = ''

    print hotel_name
    print source_id
    print brand_name
    print map_info
    print address
    print city
    print country
    print city_id
    print star
    print service
    print img_items
    print description
    print check_in_time
    print check_out_time

    data = (
        hotel_name, hotel_name_en, source, source_id, brand_name, map_info, address, city, country, city_id,
        star,
        service,
        img_items, description, check_in_time, check_out_time)
    return data


def insert_data(args):
    """
    插入 hotel 数据
    :param args: hotel 信息 tuple
    :return: 本次插入结果
    """
    sql = 'insert into hotelinfo_1010(`hotel_name`,`hotel_name_en`,`source`,`source_id`,`brand_name`,`map_info`,`address`,`city`,`country`,`city_id`,`star`,`service`,`img_items`,`description`,`check_in_time`,`check_out_time`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
    return db.ExecuteSQLs(sql, args)


def get_task_new():
    """
    获取未抓取的 hotel_id
    :return:每一个 hotel_id 的迭代对象
    """
    sql = 'select hotel_id from hotel_id_total_test where hotel_id not in (select source_id from hotelinfo_1010);'
    for line in db.QueryBySQL(sql):
        yield line['hotel_id']
