from __future__ import absolute_import

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
                              # 'proj.hotel_list_task',
                              'proj.qyer_attr_task',
                              'proj.poi_nearby_city_task',
                              'proj.daodao_img_rename_tasks',
                              # 'proj.hotel_tax_task',
                              'proj.suggestion_task',
                              'proj.full_website_spider_task',
                              'proj.tripadvisor_list_tasks',
                              'proj.file_downloader_task',
                              'proj.tripadvisor_website_task'
                              ])
app.config_from_object('proj.config')
app.conf.update(
    CELERY_QUEUES=(
        Queue('hotel_suggestion', exchange=Exchange('hotel_suggestion', type='direct'), routing_key='hotel_suggestion'),
        Queue('full_site_task', exchange=Exchange('full_site_task', type='direct'), routing_key='full_site_task'),
        Queue('hotel_task', exchange=Exchange('hotel_task', type='direct'), routing_key='hotel_task'),
        Queue('hotel_list_task', exchange=Exchange('hotel_list_task', type='direct'), routing_key='hotel_list_task'),
        Queue('tripadvisor_list_tasks', exchange=Exchange('tripadvisor_list_tasks', type='direct'),
              routing_key='tripadvisor_list_tasks'),
        Queue('file_downloader', exchange=Exchange('file_downloader', type='direct'),
              routing_key='file_downloader'),
        Queue('tripadvisor_website', exchange=Exchange('tripadvisor_website', type='direct'),
              routing_key='tripadvisor_website'),
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
    handler = RotatingFileHandler(
        '/search/log/celery.log',
        maxBytes=100 * 1024 * 1024,
        backupCount=10
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
