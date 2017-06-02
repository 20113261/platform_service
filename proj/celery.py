from __future__ import absolute_import

from celery import Celery
from celery.signals import setup_logging
import logging
from logging.handlers import RotatingFileHandler
import mioji.common.logger

app = Celery('proj', include=['proj.tasks',
                              'proj.hotel_tasks',
                              'proj.poi_pic_spider_tasks',
                              'proj.qyer_city_spider',
                              'proj.qyer_poi_tasks',
                              'proj.tripadvisor_city_query_task',
                              'proj.qyer_city_query_task',
                              'proj.tripadvisor_city',
                              # 'proj.hotel_list_task',
                              'proj.qyer_attr_task',
                              'proj.poi_nearby_city_task',
                              'proj.daodao_img_rename_tasks',
                              #'proj.hotel_tax_task'
                              ])
app.config_from_object('proj.config')


def initialize_logger(loglevel=logging.INFO, **kwargs):
    handler = RotatingFileHandler(
        '/search/log/celery.log',
        maxBytes=100 * 1024 * 1024,
        backupCount=10
    )
    log = logging.getLogger('newframe')
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    log = logging.getLogger('celery')
    log.addHandler(handler)
    log.setLevel(loglevel)
    return log


setup_logging.connect(initialize_logger)

if __name__ == '__main__':
    app.start()
