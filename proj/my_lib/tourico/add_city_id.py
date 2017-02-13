# coding=utf-8
"""
    @author: HouRong
    @description:
    通过距离和产品标注的名称对应关系更新 city_id
"""
import math
from collections import defaultdict

import db_devdb

import tourico.hotel_info.database as db

TABLE = 'hotelinfo_1010'

CITY_DICT = {
    'Merida': ['11431'],
    'Mar Del Plata': ['60020'],
    'Dar Es Salaam': ['40067'],
    'Iguazu': ['60008', '60010'],
    'Melaka': ['20209'],
    'North Little Rock': ['50108'],
    'Carmel': ['50129'],
    'Newcastle': ['30011'],
    'Nevsehir': ['11501'],
    "Saint John's": ['50746'],
    'Gothenburg': ['10104'],
    'Genoa': ['10101'],
    'Puebla': ['50758'],
    'Bruges': ['10041'],
    'Grand Canyon': ['50743'],
    'Saint Louis': ['50123'],
    'Istanbul': ['10605'],
    'Quebec': ['50045'],
    'Rio De Janeiro': ['60003'],
    'Salerno': ['10407'],
    'Playa del Carmen': ['50752'],
    'Marrakech': ['40014']
}


# lon lat
def get_distance(lon_1, lat_1, lon_2, lat_2):
    """
    从经纬度获取距离
    :param lon_1: 1经度
    :param lat_1: 1纬度
    :param lon_2: 2经度
    :param lat_2: 2纬度
    :return:
    """
    R = 6371.0
    X1 = float(lon_1) * 3.14 / 180
    Y1 = float(lat_1) * 3.14 / 180

    X2 = float(lon_2) * 3.14 / 180
    Y2 = float(lat_2) * 3.14 / 180

    distance = R * math.acos(math.cos(Y1) * math.cos(Y2) * math.cos(X1 - X2) + math.sin(Y1) * math.sin(Y2))
    return distance


def get_dict():
    id_dict = defaultdict(list)
    sql = 'select id,name_en,map_info from city'
    for line in db_devdb.QueryBySQL(sql):
        id_dict[line['name_en']].append((line['map_info'], line['id']))
    return id_dict


def get_id_map_dict():
    id_map_dict = {}
    sql = 'select id,map_info from city'
    for line in db_devdb.QueryBySQL(sql):
        id_map_dict[line['id']] = line['map_info']
    return id_map_dict


def get_local_dict():
    local_dict = defaultdict(list)
    id_map_dict = get_id_map_dict()
    for k, v in CITY_DICT.items():
        local_dict[k] = map(lambda x: (id_map_dict[x], x), v)
    return local_dict


def get_task():
    sql = 'select source_id,city,map_info from {0}'.format(TABLE)
    for line in db.QueryBySQL(sql):
        yield line['source_id'], line['city'], line['map_info']


def update_city_id(args):
    sql = 'update {0} set city_id=%s where source_id=%s'.format(TABLE)
    return db.ExecuteSQLs(sql, args)


if __name__ == '__main__':
    id_dict = get_dict()
    local_dict = get_local_dict()
    datas = []
    count = 0
    for source_id, city, map_info in get_task():
        cities = id_dict[city]
        if not cities:
            cities = id_dict[city.replace(' City', '').replace('  ', ' ')]
        if not cities:
            cities = id_dict[city.replace('\'', '').replace('  ', ' ')]
        if not cities:
            cities = id_dict[city.replace('-', ' ').replace('  ', ' ')]
        if not cities:
            cities = id_dict[city.replace('\'', '').replace(' City', '').replace('-', ' ').replace('  ', ' ')]
        if not cities:
            cities = local_dict[city]
        if not cities:
            continue
        else:
            for c in cities:
                if c[0] == 'NULL' or get_distance(map_info.split(',')[0], map_info.split(',')[1], c[0].split(',')[0],
                                                  c[0].split(',')[1]) <= 50:
                    datas.append((c[1], source_id))
                    count += 1
                    print count
                    if count % 1000 == 0:
                        update_city_id(datas)
                        datas = []
                        print count
                    break
    update_city_id(datas)
    print count
