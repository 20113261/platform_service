#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/16 下午4:43
# @Author  : Hou Rong
# @Site    : 
# @File    : total_tasks.py
# @Software: PyCharm
from __future__ import absolute_import
from SDK import *
from SDK.SupplementTask import SupplementReMapInfo
from SDK.HiltonTaxSDK import HiltonTaxSDK
from SDK.PoiCtripListSDK import PoiCtripListSDK
from SDK.PoiCtripDetailSDK import PoiCtripDetailSDK
from SDK.GTListSDK import GTListSDK
from SDK.GTDetailSDK import GTDetailSDK
from SDK.PoiSourceListSDK import PoiSourceListSDK
from SDK.PoiSourceDetailSDK import PoiSourceDetailSDK
from SDK.CtripImageSDK import  CtripImageSDK
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask


#ctripPoi image task
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='20/m')
def ctripPoi_image_task(self, task, **kwargs):
    _sdk = CtripImageSDK(task=task)
    return _sdk.execute()
# -- poi all task
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='25/m')
def PoiSource_detail_task(self, task, **kwargs):
    _sdk = PoiSourceDetailSDK(task=task)
    return _sdk.execute()
#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='20/m')
def PoiSource_list_task(self, task, **kwargs):
    _sdk = PoiSourceListSDK(task=task)
    return _sdk.execute()

# -- grouptravel all task
@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='20/m')
def GT_detail_task(self, task, **kwargs):
    _sdk = GTDetailSDK(task=task)
    return _sdk.execute()
#
#
@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='30/s')
def GT_list_task(self, task, **kwargs):
    _sdk = GTListSDK(task=task)
    return _sdk.execute()

# -- ctrip poi 以后并入 poisourcetask
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='20/m')
def ctrip_poi_detail_task(self, task, **kwargs):
    _sdk = PoiCtripDetailSDK(task=task)
    return _sdk.execute()
#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='20/m')
def ctrip_poi_list_task(self, task, **kwargs):
    _sdk = PoiCtripListSDK(task=task)
    return _sdk.execute()


#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='5/s')
def qyer_list_task(self, task, **kwargs):
    _sdk = QyerListSDK(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='20/m')
def poi_list_task(self, task, **kwargs):
    _sdk = PoiListSDK(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='60/s')
def hotel_img_merge_task(self, task, **kwargs):
    _sdk = HotelImgMergeSDK(task=task)
    return _sdk.execute()


#
#


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='25/m')
def hotel_list_task(self, task, **kwargs):
    _sdk = HotelListSDK(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='20/m')
def slow_hotel_list_task(self, task, **kwargs):
    _sdk = HotelListSDK(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='10/m')
def qyer_detail_task(self, task, **kwargs):
    _sdk = QyerDetailSDK(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/m')
def poi_detail_task(self, task, **kwargs):
    _sdk = PoiDetailSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='3/s')
def hotel_detail_task(self, task, **kwargs):
    _sdk = HotelDetailSDK(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='20/m')
def slow_hotel_detail_task(self, task, **kwargs):
    _sdk = HotelDetailSDK(task=task)
    return _sdk.execute()


#
#

@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='5/m')
def images_task(self, task, **kwargs):
    _sdk = ImagesSDK(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='13/s')
def crawl_json(self, task, **kwargs):
    _sdk = CrawlJson(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def supplement_map_info(self, task, **kwargs):
    _sdk = SupplementMapInfo(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='1/m')
def supplement_remap_info(self, task, **kwargs):
    _sdk = SupplementReMapInfo(task=task)
    return _sdk.execute()


#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def supplement_daodao_img(self, task, **kwargs):
    _sdk = SupplementDaodaoImg(task=task)
    return _sdk.execute()


#
#
# @app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='20/m')
# def qyer_city_task(self, task, **kwargs):
#     _sdk = QyerCitySDK(task=task)
#     return _sdk.execute()
#
#
# @app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='5/s')
# def baidu_search_task(self, task, **kwargs):
#     _sdk = BaiDuSearchSDK(task=task)
#     return _sdk.execute()
#
#
# @app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='5/s')
# def ihg_city_suggest(self, task, **kwargs):
#     _sdk = IhgCitySDK(task=task)
#     return _sdk.execute()
#
#
@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='25/m')
def ks_move_task(self, task, **kwargs):
    _sdk = KsMoveSDK(task=task)
    return _sdk.execute()


#
# @app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='1/s')
# def Accor_city_suggest(self, task, **kwargs):
#     _sdk = AccorCitySDK(task=task)
#     return _sdk.execute()
#
#
# @app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='50/m')
# def european_trail_task(self, task, **kwargs):
#     _sdk = EuropeStationSDK(task=task)
#     return _sdk.execute()
#
# @app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='5/s')
# def Marriott_city_task(self, task, **kwargs):
#     _sdk = MarriottCitySDK(task=task)
#     return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='5/s')
def normal_city_task(self, task, **kwargs):
    _sdk = NormalTaskSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=5, rate_limit='30/m')
def slow_city_task(self, task, **kwargs):
    _sdk = SlowTaskSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='1/m')
def hilton_tax_task(self, task, **kwargs):
    _sdk = HiltonTaxSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='1/m')
def veriflight_task(self, task, **kwargs):
    _sdk = VeriFlightSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='13/s')
def google_drive_task(self, task, **kwargs):
    _sdk = GoogleDriveSDK(task=task)
    return _sdk.execute()

@app.task(bind=True, base=BaseTask, max_retires=3, rate_limit='30/m')
def allhotel_city_suggest(self,task,**kwargs):
    _sdk = AllHotelSourceSDK(task=task)
    return _sdk.execute()