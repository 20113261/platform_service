#!/usr/bin/env python
# -*- coding: utf-8 -*-

from util import SkipException
from pymongo import MongoClient

mongo = MongoClient('mongodb://root:miojiqiangmima@10.10.114.244')

tickets_fun = mongo['huantaoyou']['tickets_fun']
view_ticket = mongo['huantaoyou']['view_ticket']    # 门票 3
activity_ticket = mongo['huantaoyou']['activity_ticket']   # 当地美食 1  休闲娱乐 2
tour_ticket = mongo['huantaoyou']['tour_ticket']   # 一日游  4
play_ticket = mongo['huantaoyou']['play_ticket']    #

attractions = mongo['huantaoyou']['found_attraction']
mioji_poi = mongo['huantaoyou']['attraction']


def get_database(name):
    return mongo[name]


def get_collection(name, dbname=None):
    if not dbname:
        dbname = 'huantaoyou'
    return mongo[dbname][name]


def get_ref_poi(my_id):
    if isinstance(my_id, int):
        ret = attractions.find_one({'consumer_terminal_id': int(my_id)})
        if isinstance(ret, dict):
            return ret


def get_mioji_poi(poi_id):
    # if poi_id == '':
    ret = mioji_poi.find_one({'id': poi_id})
    if ret:
        return ret
    raise Exception('肯定有东西出错了')
