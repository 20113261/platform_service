from __future__ import absolute_import

from celery import Celery

app = Celery('proj', include=['proj.tasks',
                              'proj.hotel_tasks',
                              'proj.poi_pic_spider_tasks',
                              'proj.qyer_city_spider',
                              'proj.qyer_poi_tasks',
                              'proj.tripadvisor_city_query_task',
                              'proj.qyer_city_query_task',
                              'proj.tripadvisor_city',
                              'proj.hotel_list_task',
                              'proj.qyer_attr_task',
                              'proj.poi_nearby_city_task',
                              'proj.daodao_img_rename_tasks'
                              ])
app.config_from_object('proj.config')

if __name__ == '__main__':
    app.start()
