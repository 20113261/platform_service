#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/24 上午9:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm

import datetime
import time
import traceback
from itertools import repeat

import pymysql

from send_task import send_hotel_detail_task, send_poi_detail_task, send_qyer_detail_task, send_image_task

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine('mysql+pymysql://mioji_admin:mioji1109@10.10.228.253:3306/ServicePlatform?charset=utf8',
                       encoding="utf-8", pool_size=100, pool_recycle=3600, echo=False)
DBSession = sessionmaker(bind=engine)
session = DBSession()
HOTEL_SOURCE = ('agoda', 'booking', 'ctrip', 'elong', 'expedia', 'hotels', 'hoteltravel', 'hrs', 'cheaptickets', 'orbitz',
        'travelocity', 'ebookers', 'tripadvisor', 'ctripcn', 'hilton')
POI_SOURCE = 'daodao'
QYER_SOURCE = 'qyer'
# TODO  所有表的update_time字段加索引
# TODO  所有表的update_time字段改为timestramp(6)类型

def get_default_timestramp():
    return datetime.datetime(year=1970, month=2, day=4, hour=6, minute=8, second=10, microsecond=666666)

def get_seek(task_name):
    sql = """select seek from task_seek where task_name = '%s'"""
    result = session.execute(sql % task_name)
    timestramp = result.fetchone()
    print type(timestramp), timestramp
    if not timestramp or len(timestramp)==0:
        return get_default_timestramp()

    return timestramp[0]

def update_seek(task_name, seek):
    sql = """replace into task_seek (task_name, seek) values('%s','%s');"""
    print sql % (seek, task_name)
    session.execute(sql % (seek, task_name))
    session.commit()

def get_all_tables():
    # TODO  建一个针对information_schema的DBSession
    sql = """select table_name from information_schema.tables where table_schema = 'ServicePlatform';"""
    return session.execute(sql)

def create_table(table_name):
    conn = pymysql.connect(host='10.10.228.253', user='mioji_admin', password='mioji1109', charset='utf8',
                           db='ServicePlatform')
    cursor = conn.cursor()
    with open('../../detail.sql') as f:
        sql = f.read()
        cursor.execute(sql % table_name)
        cursor.close()
        conn.close()

def monitoring_hotel_list2detail():
    # TODO  hotel_list_task任务需要修改为入mysql，  hotel_suggestions_city需要添加时间戳字段
    sql = """select source, source_id, city_id, hotel_url, utime from %s where utime > '%s' order by utime"""
    table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

    for table_name in table_dict.keys():

        tab_args = table_name.split('_')
        if tab_args[0] != 'list': continue
        if tab_args[1] != 'hotel': continue
        if tab_args[2] not in HOTEL_SOURCE: continue

        timestamp = get_seek(table_name)

        detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
        if table_dict.get(detail_table_name, True):
            create_table(detail_table_name)

        try:
            timestamp = send_hotel_detail_task(session.execute(sql % ('ServicePlatform.' + table_name, timestamp)), table_name)
            print timestamp
            if timestamp is not None:
                update_seek(table_name, timestamp)
        except Exception as e:
            print traceback.format_exc(e)

def monitoring_hotel_detail2ImgOrComment():
    #  TODO 修改get_images task  hotel保留之后的，poi保留之前的
    sql = """select source, source_id, city_id, hotel_url, update_time from %s where update_time > '%s' order by update_time"""
    for (table_name,) in get_all_tables():

        tab_args = table_name.split('_')
        if tab_args[0] != 'detail': continue
        if tab_args[1] != 'hotel': continue
        if tab_args[2] not in HOTEL_SOURCE: continue

        timestamp = get_seek(table_name)
        try:
            timestamp = send_image_task(session.execute(sql % ('ServicePlatform.' + table_name, timestamp)), table_name,
                                        is_poi_task=False)
            if timestamp is not None:
                update_seek(table_name, timestamp)
        except Exception as e:
            print traceback.format_exc(e)

def monitoring_poi_list2detail():
    # TODO poi详情任务改为一个task
    sql = """select source, source_id, city_id, hotel_url, utime from %s where utime > '%s' order by utime"""

    table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

    for table_name in table_dict.keys():

        tab_args = table_name.split('_')
        if tab_args[0] != 'list': continue
        if tab_args[1] not in ('rest', 'attr', 'shop'): continue
        if tab_args[2] != POI_SOURCE: continue


        timestamp = get_seek(table_name)

        detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
        if table_dict.get(detail_table_name, True):
            create_table(detail_table_name)
        try:
            timestamp = send_poi_detail_task(session.execute(sql % ('ServicePlatform.' + table_name, timestamp)), table_name)
            if timestamp is not None:
                update_seek(table_name, timestamp)
        except Exception as e:
            print traceback.format_exc(e)

def monitoring_poi_detail2imgOrComment():
    sql = """select source, source_id, city_id, hotel_url, update_time from %s where update_time > '%s' order by update_time"""
    for (table_name,) in get_all_tables():

        tab_args = table_name.split('_')
        if tab_args[0] != 'detail': continue
        if tab_args[1] not in ('rest', 'attr', 'shop'): continue
        if tab_args[2] != POI_SOURCE: continue

        timestamp = get_seek(table_name)

        try:
            timestamp = send_image_task(session.execute(sql % ('ServicePlatform.' + table_name, timestamp)), table_name,
                                        is_poi_task=True)
            if timestamp is not None:
                update_seek(table_name, timestamp)
        except Exception as e:
            print traceback.format_exc(e)

def monitoring_qyer_list2detail():
    # TODO poi详情任务改为一个task
    sql = """select source, source_id, city_id, hotel_url, utime from %s where utime > '%s' order by utime"""

    table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

    for table_name in table_dict.keys():

        tab_args = table_name.split('_')
        if tab_args[0] != 'list': continue
        if tab_args[1] != 'total': continue
        if tab_args[2] != QYER_SOURCE: continue

        timestamp = get_seek(table_name)

        detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
        if table_dict.get(detail_table_name, True):
            create_table(detail_table_name)
        try:
            timestamp = send_qyer_detail_task(session.execute(sql % ('ServicePlatform.' + table_name, timestamp)), table_name)
            if timestamp is not None:
                update_seek(table_name, timestamp)
        except Exception as e:
            print traceback.format_exc(e)

def test_timstramp():
    sql_sel = """select source_id from routine_hotel_list"""
    sql_upd = """update routine_hotel_list set utime = '%s' where source_id = '%s'"""
    ids = session.execute(sql_sel)
    for id in ids.fetchall():
        time.sleep(0.2)
        session.execute(sql_upd % (datetime.datetime.now(), id[0]))
    session.commit()

if __name__ == '__main__':
    # get_default_timestramp()
    # get_seek('hotel_list2detail')
    # update_seek('hotel_list2detail', datetime.datetime.now())
    # test_timstramp()
    # monitoring_hotel_list2detail()
    monitoring_hotel_detail2ImgOrComment()