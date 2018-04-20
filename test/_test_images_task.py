#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/11 上午9:10
# @Author  : Hou Rong
# @Site    : 
# @File    : test_images_task.py
# @Software: PyCharm
import sys

# sys.path.append('/data/lib')
print(sys.path)
from proj.my_lib.Common.Task import Task
from proj.total_tasks import images_task

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

    # get_images(
    #     **{
    #         'source': "daodao",
    #         'new_part': "detail_rest_daodao_20170928a",
    #         'target_url': "https://ccm.ddcdn.com/ext/photo-w/05/9d/be/f4/spaghetti-ai-ricci-di.jpg",
    #         'desc_path': "/data/nfs/image/img_rest_daodao_20170928a_filter",
    #         'is_poi_task': True,
    #         'source_id': "4697785",
    #         'part': "20170928a",
    #         'file_path': "/data/nfs/image/img_rest_daodao_20170928a",
    #         "task_name": "images_rest_daodao_20170928a",
    #         "task_response": TaskResponse()
    #     }
    # )

    # get_images(
    #     **{
    #         'source': "huantaoyou",
    #         'new_part': "image_wanle_huantaoyou_20171023a",
    #         'target_url': "http://img.huantaoyou.com/PUB/TH/TH00194/IM_3469e694e140462c93829c3469a69084.png",
    #         'desc_path': "/data/nfs/image/img_wanle_huantaoyou_20171023a_filter",
    #         'is_poi_task': True,
    #         'source_id': "test",
    #         'part': "20171023a",
    #         'file_path': "/data/nfs/image/img_wanle_huantaoyou_20171023a",
    #         "task_name": "image_wanle_huantaoyou_20171023a",
    #         "task_response": TaskResponse()
    #     }
    # )

    # get_images(
    #     **{
    #         'source': "ctrip",
    #         'new_part': "detail_hotel_ctrip_20170929a",
    #         'target_url': "//dimg04.c-ctrip.com/images/220n0h0000008txhgD341_W_1600_1200_Q70.jpg",
    #         'desc_path': "/data/nfs/image/img_hotel_ctrip_20170929a_filter",
    #         'is_poi_task': False,
    #         'source_id': "7491732",
    #         'part': "20170929a",
    #         'file_path': "/data/nfs/image/img_hotel_ctrip_20170929a",
    #         "task_name": "images_hotel_ctrip_20170929a",
    #         "task_response": TaskResponse()
    #     }
    # )
    task = Task(_worker='proj.total_tasks.images_task', _task_id='176ddbc7960c2a6f6d8d7c9baea65617', _source='tuniuGT',
                _type='DownloadImages',
                _task_name='image_GT_tuniu_20180414',
                _used_times=0, max_retry_times=6,
                # kwargs={"source": "daodao", "new_part": "detail_attr_daodao_20171122a",
                #         "target_url": "https://ccm.ddcdn.com/ext/photo-s/0f/dd/44/61/peaceful-time.jpg",
                #         "source_id": "test", "bucket_name": "mioji-attr", "is_poi_task": True, "part": "20171122a",
                #         "file_prefix": ""},
                # kwargs={
                #     "source": "ihg",
                #     "new_part": "detail_hotel_ihg_20171220a",
                #     "target_url": "https://ihg.scene7.com/is/image/ihg/candlewood-suites-idaho-falls-3053752126-4x3?fmt=png-alpha",
                #     "source_id": "idapd",
                #     "bucket_name": "mioji-hotel",
                #     "is_poi_task": False,
                #     "part": "20171220a",
                #     "file_prefix": ""
                # },
                kwargs={
                    'file_prefix': 'tuniuGT',
                    'target_url': "https://m.tuniucdn.com//fb2/t1/G3/M00/3D/0B/Cii_LlloJcyIGfs2AFyrXaRNclAAADnOgNM364AXKt1824_w640_h480_c1_t0.jpg",
                    'source_id': "210138695",
                    'need_insert_db': True,
                    'source': "tuniuGT",
                    'bucket_name': 'mioji-grouptravel',
                    'is_poi_task': True,
                },
                _queue='file_downloader', _routine_key='file_downloader',
                list_task_token='', task_type=0
                )
    # kwargs={'source': "huantaoyou",
    #         'new_part': "image_wanle_huantaoyou_20171023a",
    #         'target_url': "http://img.huantaoyou.com/PUB/TH/TH00194/IM_3469e694e140462c93829c3469a69084.png",
    #         'is_poi_task': True,
    #         'source_id': "test",
    #         'part': "20171023a",
    #         'bucket_name': 'mioji-wanle',
    #         'file_prefix': 'anc'
    #         })
    images_task(task=task)
