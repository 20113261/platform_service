# coding=utf-8
import math
import pymysql
from city_info import cid2map, special_city

# distance
EARTH_RADIUS = 6378137
PI = 3.1415927


def rad(d):
    return d * PI / 180.0


def getDist(lng1, lat1, lng2, lat2):
    radLat1 = rad(lat1)
    radLat2 = rad(lat2)
    a = radLat1 - radLat2
    b = rad(lng1) - rad(lng2)

    s = 2 * math.asin(
        math.sqrt(
            math.pow(math.sin(a / 2), 2) + math.cos(radLat1) * math.cos(radLat2) * math.pow(math.sin(b / 2), 2)))

    s *= EARTH_RADIUS
    s = round(s * 10000) / 10000

    return int(s)


def getDistSimply(lng1, lat1, lng2, lat2):
    dx = lng1 - lng2
    dy = lat1 - lat2
    b = (lat1 + lat2) / 2.0
    lx = rad(dx) * EARTH_RADIUS * math.cos(rad(b))
    ly = EARTH_RADIUS * rad(dy)
    return int(math.sqrt(lx * lx + ly * ly))


def get_dist_by_map(map_1, map_2):
    try:
        return getDistSimply(map_1[0], map_1[1], map_2[0], map_2[1])
    except Exception as e:
        # print(str(e))
        return 100000000000


def get_map_diff(map_info_1, map_info_2):
    diff = abs(map_info_1[0] - map_info_2[0]) + abs(map_info_1[1] - map_info_2[1])
    return diff


def get_nearby_city(poi_id, poi_city_id, poi_map_info):
    try:
        poi_lgt, poi_lat = poi_map_info.strip().split(',')
        poi_lgt_lat = (float(poi_lgt), float(poi_lat))
    except Exception as e:
        return ''

    is_long_dist_poi = False

    # 特殊三个洲的POI距离范围比较大
    if poi_city_id in special_city:
        is_long_dist_poi = True

    near_cid_set = set()

    for cand_cid in cid2map:
        if poi_city_id == cand_cid:
            continue

        cand_city_map = cid2map[cand_cid]

        # todo change str into tuple
        map_diff = get_map_diff(cand_city_map, poi_lgt_lat)

        if (not is_long_dist_poi and map_diff >= 1.5) or map_diff >= 5:
            continue

        # todo change str into tuple
        cand_dist = get_dist_by_map(cand_city_map, poi_lgt_lat)

        if cand_dist <= 50000:
            near_cid_set.add(cand_cid)
        elif is_long_dist_poi and cand_dist <= 250000:
            near_cid_set.add(cand_cid)

    near_cid = '|'.join(near_cid_set)

    return near_cid


def insert_db(args):
    conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', charset='utf8', db='NearByCity')
    with conn as cursor:
        sql = 'INSERT INTO NearByCity VALUES (%s,%s,%s)'
        cursor.execute(sql, args)
    conn.close()


if __name__ == '__main__':
    poi_id = 'v223168'
    city_id = '30010'
    map_info = '151.212531,-33.866978'
    nearby_city = get_nearby_city(poi_id, city_id, map_info)
    print insert_db((poi_id, city_id, nearby_city))
