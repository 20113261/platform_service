from __future__ import absolute_import

import os
from celery import Celery, platforms
from celery.app.log import TaskFormatter, get_current_task
from celery.signals import setup_logging
import logging
from logging.handlers import RotatingFileHandler

from kombu import Queue, Exchange

platforms.C_FORCE_ROOT = True

app = Celery('proj', include=['proj.tasks',
                              'proj.hotel_tasks',
                              'proj.hotel_static_tasks',
                              'proj.poi_pic_spider_tasks',
                              # 'proj.qyer_city_spider',
                              'proj.qyer_poi_tasks',
                              # 'proj.tripadvisor_city_query_task',
                              # 'proj.qyer_city_query_task',
                              'proj.tripadvisor_city',
                              'proj.hotel_list_task',
                              'proj.qyer_attr_task',
                              'proj.poi_nearby_city_task',
                              'proj.daodao_img_rename_tasks',
                              # 'proj.hotel_tax_task',
                              'proj.suggestion_task',
                              'proj.full_website_spider_task',
                              'proj.tripadvisor_list_tasks',
                              'proj.file_downloader_task',
                              'proj.tripadvisor_website_task',
                              'proj.hotel_list_routine_tasks',
                              'proj.hotel_list_rest_tasks',
                              'proj.hotel_list_view_tasks',
                              'proj.hotel_routine_tasks',
                              'proj.poi_task',
                              'proj.poi_list_task',
                              'proj.qyer_list_task',
                              'proj.supplement_mapinfo_task',
                              'proj.merge_tasks',
                              ])
app.config_from_object('proj.config')
app.conf.update(
    CELERY_QUEUES=(
        Queue('file_downloader', exchange=Exchange('file_downloader', type='direct'), routing_key='file_downloader'),
        Queue('hotel_detail', exchange=Exchange('hotel_detail', type='direct'), routing_key='hotel_detail'),
        Queue('hotel_list', exchange=Exchange('hotel_list', type='direct'), routing_key='hotel_list'),
        Queue('poi_detail', exchange=Exchange('poi_detail', type='direct'), routing_key='poi_detail'),
        Queue('poi_list', exchange=Exchange('poi_list', type='direct'), routing_key='poi_list'),
        Queue('google_api', exchange=Exchange('google_api', type='direct'), routing_key='google_api'),
        Queue('supplement_field', exchange=Exchange('supplement_field', type='direct'), routing_key='supplement_field'),
    ),

)


# class StreamToLogger(object):
#     """
#     Fake file-like stream object that redirects writes to a logger instance.
#     """
#
#     def __init__(self, logger, log_level=logging.INFO):
#         self.logger = logger
#         self.log_level = log_level
#         self.linebuf = ''
#
#     def write(self, buf):
#         for line in buf.rstrip().splitlines():
#             self.logger.log(self.log_level, line.rstrip())
#
#     def flush(self):
#         pass


class StdoutFormatter(logging.Formatter):
    """Format Log For Stdout"""

    def __init__(self):
        self.fmt = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s name[%(task_name)s]" \
                   " id[%(task_id)s] %(message)s"
        super(StdoutFormatter, self).__init__(self.fmt)

    def format(self, record):
        task = get_current_task()
        if task and task.request:
            record.__dict__.update(task_id=task.request.id,
                                   task_name=task.name)
        else:
            record.__dict__.setdefault('task_name', '???')
            record.__dict__.setdefault('task_id', '???')
            return logging.Formatter.format(self, record)


def initialize_logger(loglevel=logging.INFO, **kwargs):
    log_name = os.environ.get('CELERY_LOG_NAME', 'celery')
    handler = RotatingFileHandler(
        '/data/log/{0}.log'.format(log_name),
        maxBytes=100 * 1024 * 1024,
        backupCount=2
    )
    # fmt = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
    # formatter = logging.Formatter(fmt)
    # handler.setFormatter(formatter)

    # stdout_logger = logging.getLogger('STDOUT')
    # sl = StreamToLogger(stdout_logger, logging.INFO)
    # sys.stdout = sl
    #
    # stderr_logger = logging.getLogger('STDERR')
    # sl = StreamToLogger(stderr_logger, logging.ERROR)
    # sys.stderr = sl

    # stdout_logger.addHandler(handler)
    # stderr_logger.addHandler(handler)
    log = logging.getLogger('celery')
    log.addHandler(handler)
    log.setLevel(loglevel)
    return log


NewFrameHandler = RotatingFileHandler(
    '/data/log/service_platform/newframe.log',
    maxBytes=100 * 1024 * 1024,
    backupCount=2
)

new_frame_log = logging.getLogger('newframe')
new_frame_log.addHandler(NewFrameHandler)
new_frame_log.setLevel(logging.DEBUG)

setup_logging.connect(initialize_logger)

if __name__ == '__main__':
    app.start()
