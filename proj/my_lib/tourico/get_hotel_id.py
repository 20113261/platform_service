# coding=utf-8
"""
    @author: HouRong
    @description:
    从对方 API 获取全量的 hotel_id
"""
from suds.client import Client
from tourico_city_func import queryGetHotelsByDestination

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


def insert_hotel_id(args):
    sql = 'insert ignore into hotel_id_total_2 (`hotel_id`,`continent`,`country`,`state`,`city`,`finished_key`) VALUES (%s,%s,%s,%s,%s,%s)'
    return db.ExecuteSQLs(sql, args)


def get_total_hotel_id(res):
    """
    解析所有的 Hotel ID
    :param res: suds 对象
    :return: tourico 全量的 hotel_id
    """
    datas = []
    for continent in res.Continent:
        continent_name = continent._name
        for country in continent.Country:
            country_name = country._name
            for state in country.State:
                state_name = state._name
                for city in state.City:
                    city_name = city._name
                    try:
                        for hotel in city.Hotels.Hotel:
                            data = (hotel._hotelId, continent_name, country_name, state_name, city_name, '0')
                            datas.append(data)
                    except:
                        pass
                    try:
                        for city_location in city.CityLocation:
                            for hotel in city_location.Hotels.Hotel:
                                data = (hotel._hotelId, continent_name, country_name, state_name, city_name, '0')
                                datas.append(data)
                    except:
                        pass
    print len(datas)
    print insert_hotel_id(datas)


if __name__ == '__main__':
    # 一部分城市
    # res = queryGetHotelsByDestination('Africa', 'Egypt', '', 'Hurghada')
    # 全量城市
    res = queryGetHotelsByDestination('', '', '', '')
    get_total_hotel_id(res)
