# coding=utf-8
"""
    @author: HouRong
    @description:
    一些关于 tourico 城市抓取与解析的函数
"""
from suds.client import Client

import database as db


def get_client(url, auth):
    """
    获取 webservice client
    :param url: 对方接口 url
    :param auth: 验证信息字典
    :return: suds client
    """
    client = Client(url)
    h = client.factory.create('ns1:LoginHeader')
    for k, v in auth.items():
        h[k] = v
    client.set_options(soapheaders=h)
    return client


def queryGetHotelsByDestination(continent, country, state, city):
    """
    获取 hotel 信息
    :param continent:大陆
    :param country: 国家
    :param state: 洲/省
    :param city: 城市
    :return: suds 对象
    """
    url = 'http://destservices.touricoholidays.com/DestinationsService.svc?wsdl'
    auth = dict(username='MIO106', password='@2NzbzDU', culture='zh_CN', version='7.123')
    client = get_client(url, auth)
    destination = client.factory.create('ns1:Destination')
    destination.Continent = continent
    destination.Country = country
    destination.State = state
    destination.City = city
    destination.Providers.ProviderType = 'Default'
    destination.StatusDate = "2014-01-01"
    res = client.service.GetHotelsByDestination(destination)
    return res


def get_hotel_id(res):
    """
    获取城市中的所有酒店 id
    :param res: suds 酒店对象
    :return: 酒店 id 列表, 城市坐标
    """
    hotel_id_list = []
    city_map = ''
    try:
        for hotel in res.Continent[0].Country[0].State[0].City[0].Hotels.Hotel:
            hotel_id_list.append(hotel._hotelId)
    except:
        pass
    try:
        for city_location in res.Continent[0].Country[0].State[0].City[0].CityLocation:
            for hotel in city_location.Hotels.Hotel:
                hotel_id_list.append(hotel._hotelId)
    except:
        pass
    try:
        city_map = res.Continent[0].Country[0].State[0].City[0]._cityLongitude + ',' + \
                   res.Continent[0].Country[0].State[0].City[0]._cityLatitude
    except:
        pass
    return hotel_id_list, city_map


def insert_hotel_id(args):
    """
    插入 hotel_id
    :param args: 数据 tuple
    :return: 插入结果
    """
    sql = 'insert ignore into hotel.hotel_id_total_full (`hotel_id`,`continent`,`country`,`state`,`city`,`map_info`,`finished_key`) VALUES (%s,%s,%s,%s,%s,%s,%s)'
    return db.ExecuteSQLs(sql, args)


def insert_total_city(args):
    """
    插入城市
    :param args: 数据 tuple
    :return:  插入结果
    """
    sql = 'insert into total_city(`continent`,`country`,`state`,`city`) values (%s,%s,%s,%s)'
    return db.ExecuteSQL(sql, args)


if __name__ == '__main__':
    # test
    res = queryGetHotelsByDestination('Europe', 'France', '', 'Paris')
    # res = qyeryGetHotelsByDestination('Africa', 'Egypt', '', 'Hurghada')
    hotel_id_list, tri_code = get_hotel_id(res)
    print hotel_id_list
    print len(hotel_id_list)
    print tri_code
