import inspect
from proj.my_lib.models.base_model import BaseModel, Hotel_model

# class A():
#     def a(self):
#         i = 0
#         def b(i):
#             i+=5
#             return i
#         j = b(i)
#         print(j)
#         def c(j):
#             j+=5
#             return j
#         j = c(j)
#         print(j)
#
# aa = A()
# d = inspect.getfile(aa.a)
# print(d)
# print(inspect.getfile('a'))
import datetime
import pymongo
from apscheduler.schedulers.blocking import BlockingScheduler
from my_logger import get_logger

logger = get_logger('test2')
logger.info('h')

client = pymongo.MongoClient(host='10.19.2.103')
db = client['MongoTask_Zxp']

def get_tuniuGT_img():

    # for i in db['Task_Queue_file_downloader_TaskName_image_GT_tuniu_20180414'].find({}).


sche = BlockingScheduler()

sche.add_job(get_tuniuGT_img, 'cron', second='*/5', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=2),
                 id='monitoring_hotel_list')
sche.start()