#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/11 上午9:10
# @Author  : Hou Rong
# @Site    : 
# @File    : test_get_image.py
# @Software: PyCharm
from proj.tasks import get_images
from proj.my_lib.BaseTask import TaskResponse

if __name__ == '__main__':
    get_images(
        **{
            'source': "booking",
            'new_part': "detail_hotel_booking_20170929a",
            'target_url': "https://q.bstatic.com/images/hotel/max1024x768/135/13504008.jpg",
            'desc_path': "/data/nfs/image/img_hotel_booking_20170929a_filter",
            'is_poi_task': False,
            'source_id': "287127",
            'part': "20170929a",
            'file_path': "/data/nfs/image/img_hotel_booking_20170929a",
            "task_name": "images_hotel_booking_20170929a",
            "task_response": TaskResponse()
        }
    )
