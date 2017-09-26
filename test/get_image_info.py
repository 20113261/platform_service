#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/23 下午5:43
# @Author  : Hou Rong
# @Site    : 
# @File    : get_image_info.py
# @Software: PyCharm
from proj.tasks import get_images

# if __name__ == '__main__':
get_images(
    target_url='https://r-ec.bstatic.com/images/hotel/max1024x768/299/29970447.jpg',
    desc_path='/data/nfs/image/img_hotel_booking_20170919f_filter',
    source='booking',
    source_id='842066',
    is_poi_task=False,
    retry_count=0,
    max_retry_times=6,
    task_name='images_hotel_booking_20170919f',
    file_path='/data/nfs/image/img_hotel_booking_20170919f',
    part='20170919f'
)
