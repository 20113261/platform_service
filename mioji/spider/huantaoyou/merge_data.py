#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    import simplejson as json
except:
    import json
from mongo import get_collection
from geopy.distance import vincenty

with open('poi_collection') as fp:
    poi_collection = json.load(fp)
print '共有xxx', len(poi_collection)

attraction = get_collection('attraction')
raw_poi = get_collection('raw_poi')
city_relation = get_collection('city_relation')
country_relation = get_collection('country_relation')

found_attraction = get_collection('found_attraction')
found_raw_attraction = get_collection('found_raw_attraction')
not_found_attraction = get_collection('not_found_attraction')
one_to_multi = get_collection('one_to_multi')


not_duplicated = set()


# 欢逃游id 到 mioj的id
def get_city_id(thrid_city_id):
    city_id = city_relation.find_one({"city_id": thrid_city_id})['mioji_id']
    # country_id = country_relation.find_one('country_id': thrid_country_id)['mid']
    return city_id


def do_clear():
    found_attraction.delete_many({})
    found_raw_attraction.delete_many({})
    not_found_attraction.delete_many({})


def merge_by_attribute():
    succ_cnt = 0
    fail_cnt = 0
    do_clear()
    for item in poi_collection:
        if not item or item['consumer_terminal_id'] in not_duplicated:
            continue
        if do_merge(item):
            succ_cnt += 1
        else:
            fail_cnt += 1
        print "成功 {0}， 失败 {1}".format(succ_cnt, fail_cnt)
        not_duplicated.add(item['consumer_terminal_id'])


def do_comparsion(poi, name_cn, name_en):
    if poi['chinese_name'] == name_cn:
        return True
    if poi['english_name'] == name_en:
        return True
    return False


def do_merge(poi):
    city_id = poi['city_id']
    try:
        city_id = get_city_id(city_id)
    except:
        print poi['consumer_terminal_id'], poi['chinese_name']
        return False

    query_fliter = {
        'city_id': city_id,
    }
    cursor = attraction.find(query_fliter)

    for att in cursor:
        name_cn, name_en = att['name_cn'], att['name_en']
        if do_comparsion(poi, name_cn, name_en):
            poi['relation'] = att['id']
            try:
                found_attraction.insert_one(poi)
            except:
                pass
            return True

    cursor = raw_poi.find(query_fliter)
    for att in cursor:
        name_cn, name_en = att['name'], att['name_en']
        if do_comparsion(poi, name_cn, name_en):
            verify_query = {
                'id': att['id']
            }
            cursor = attraction.find_one(verify_query)
            if not cursor:
                continue

            poi['relation'] = att['id']
            try:
                found_raw_attraction.insert_one(poi)
                return True
            except:
                pass
    not_found_attraction.insert_one(poi)
    return False


def merge_by_gps_coordinate(item):
    location_a = (item['longitude'], item['latitude'])

    query_fliter = {
        'city_name_en': item['city_enname']
    }
    closest = (100000, None)
    cursor = attraction.find(query_fliter)
    for attr in cursor:
        attr_coordinate = map(float, attr['coordinate'].split(','))
        dist = vincenty(location_a, attr_coordinate).kilometers
        if dist < closest:
            closest = (dist, attr)

    if closest[1]:
        attr = closest[1]
        attraction_id = attr['id']
        item['relation'] = attraction_id
        found_attraction.insert_one(item)
        return True
    return False


if __name__ == '__main__':
    merge_by_attribute()
