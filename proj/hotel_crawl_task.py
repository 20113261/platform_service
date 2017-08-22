import time
import traceback

from common.common import update_proxy

from proj.celery import app
from my_lib.hotel_crawl_task.booking_crawl import booking_list_crawl, booking_detail_crawl


# todo add crawl task
@app.task(bind=True, max_retries=6, rate_limit='15/s')
def booking_list_task(self, task):
    try:
        result = booking_list_crawl(task=task)
        if not result:
            x = time.time()
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            x = time.time()
            print "Success with " + PROXY + ' CODE 0'
            update_proxy('Platform', PROXY, x, '0')
        return result
    except Exception as exc:
        x = time.time()
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=traceback.format_exc(exc))


# todo add crawl task
@app.task(bind=True, max_retries=6, rate_limit='15/s')
def booking_detail_task(self, url, task):
    try:
        result = booking_detail_crawl()
        if not result:
            x = time.time()
            update_proxy('Platform', PROXY, x, '23')
            self.retry()
        else:
            x = time.time()
            print "Success with " + PROXY + ' CODE 0'
            update_proxy('Platform', PROXY, x, '0')
        return result
    except Exception as exc:
        x = time.time()
        update_proxy('Platform', PROXY, x, '23')
        self.retry(exc=traceback.format_exc(exc))
