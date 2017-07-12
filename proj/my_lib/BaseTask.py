import pymysql
import json
import redis
import socket
import time
from celery.app.log import get_logger
from celery.task import Task

logger = get_logger(__name__)

FAILED_TASK_BLACK_LIST = {'proj.full_website_spider_task.full_site_spider'}


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    res = s.getsockname()[0]
    s.close()
    return res


class BaseTask(Task):
    default_retry_delay = 1
    max_retries = 3

    def on_success(self, retval, task_id, args, kwargs):
        print 'on success called'
        r = redis.Redis(host='10.10.180.145', db=3)
        r.incr(self.name + '|_||_|' + get_local_ip() + '|_||_|success')

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        if self.name not in FAILED_TASK_BLACK_LIST:
            conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='Task', charset='utf8')
            with conn as cursor:
                celery_task_id = task_id
                task_id = kwargs.get('task_id', '')
                kwargs.pop('task_id', None)
                kwargs['local_ip'] = get_local_ip()
                kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
                try:
                    cursor.execute(
                        'INSERT INTO FailedTask(`id`, `task_id`, `args`, `kwargs`, error_info) VALUES (%s,%s,%s,%s,%s)',
                        (task_id, celery_task_id, str(args), json.dumps(kwargs), str(einfo)))
                except Exception as e:
                    logger.exception(str(e))
            conn.close()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print 'on failure called'
        r = redis.Redis(host='10.10.180.145', db=3)
        r.incr(self.name + '|_||_|' + get_local_ip() + '|_||_|failure')

        if self.name not in FAILED_TASK_BLACK_LIST:
            conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='Task', charset='utf8')
            with conn as cursor:
                celery_task_id = task_id
                task_id = kwargs.get('task_id', '')
                kwargs.pop('task_id', None)
                try:
                    cursor.execute(
                        'INSERT INTO FailedTask(`id`, `task_id`, `args`, `kwargs`, error_info) VALUES (%s,%s,%s,%s,%s)',
                        (task_id, celery_task_id, str(args), json.dumps(kwargs), str(einfo)))
                except Exception as exception:
                    logger.exception(str(exception.message))

            conn.close()


if __name__ == '__main__':
    pass
