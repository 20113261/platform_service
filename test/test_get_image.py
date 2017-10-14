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
    # get_images(
    #     **{
    #         'source': "booking",
    #         'new_part': "detail_hotel_booking_20170929a",
    #         'target_url': "https://q.bstatic.com/images/hotel/max1024x768/135/13504008.jpg",
    #         'desc_path': "/data/nfs/image/img_hotel_booking_20170929a_filter",
    #         'is_poi_task': False,
    #         'source_id': "287127",
    #         'part': "20170929a",
    #         'file_path': "/data/nfs/image/img_hotel_booking_20170929a",
    #         "task_name": "images_hotel_booking_20170929a",
    #         "task_response": TaskResponse()
    #     }
    # )

    # get_images(
    #     **{
    #         'source': "daodao",
    #         'new_part': "detail_attr_daodao_20171010a",
    #         'target_url': "https://ccm.ddcdn.com/ext/photo-s/0e/10/3c/6e/the-much-photographed.jpg",
    #         'desc_path': "/data/nfs/image/img_attr_daodao_20171010a_filter",
    #         'is_poi_task': True,
    #         'source_id': "7753114",
    #         'part': "20171010a",
    #         'file_path': "/data/nfs/image/img_attr_daodao_20171010a",
    #         "task_name": "images_hotel_booking_20170929a",
    #         "task_response": TaskResponse()
    #     }
    # )

    # get_images(
    #     **{
    #         'source': "booking",
    #         'new_part': "detail_hotel_booking_20170929a",
    #         'target_url': "https://s-ec.bstatic.com/images/hotel/max1024x768/337/33766112.jpg",
    #         'desc_path': "/data/nfs/image/img_hotel_booking_20170929a_filter",
    #         'is_poi_task': False,
    #         'source_id': "76675",
    #         'part': "20170929a",
    #         'file_path': "/data/nfs/image/img_hotel_booking_20170929a",
    #         "task_name": "images_hotel_booking_20170929a",
    #         "task_response": TaskResponse()
    #     }
    # )

    get_images(
        **{
            'source': "daodao",
            'new_part': "detail_rest_daodao_20170928a",
            'target_url': "https://ccm.ddcdn.com/ext/photo-w/05/9d/be/f4/spaghetti-ai-ricci-di.jpg",
            'desc_path': "/data/nfs/image/img_rest_daodao_20170928a_filter",
            'is_poi_task': True,
            'source_id': "4697785",
            'part': "20170928a",
            'file_path': "/data/nfs/image/img_rest_daodao_20170928a",
            "task_name": "images_rest_daodao_20170928a",
            "task_response": TaskResponse()
        }
    )
