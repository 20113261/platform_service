import pymysql
import json
from celery.task import Task


class BaseTask(Task):
    default_retry_delay = 1
    max_retries = 3

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='Task', charset='utf8')
        with conn as cursor:
            celery_task_id = task_id
            task_id = kwargs.get('task_id', '')
            kwargs.pop('task_id', None)
            cursor.execute(
                'INSERT INTO FailedTask(`id`, `task_id`, `args`, `kwargs`, error_info) VALUES (%s,%s,%s,%s,%s)',
                (task_id, celery_task_id, str(args), json.dumps(kwargs), str(einfo)))
        conn.close()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='Task', charset='utf8')
        with conn as cursor:
            celery_task_id = task_id
            task_id = kwargs.get('task_id', '')
            kwargs.pop('task_id', None)
            cursor.execute(
                'INSERT INTO FailedTask(`id`, `task_id`, `args`, `kwargs`, error_info) VALUES (%s,%s,%s,%s,%s)',
                (task_id, celery_task_id, str(args), json.dumps(kwargs), str(einfo)))
        conn.close()


if __name__ == '__main__':
    pass
