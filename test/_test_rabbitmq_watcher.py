#coding:utf-8
import pymongo
from rabbitmq_watcher import insert_task

if __name__ == '__main__':
    client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
    db = client['MongoTask_Zxp']
    collections = db['Task_Queue_hotel_detail_TaskName_detail_hotel_hilton_20180420a']

    client_from = pymongo.MongoClient(host='10.10.231.105')
    db_from = client_from['MongoTask']
    cursor = db_from['Task_Queue_hotel_detail_TaskName_detail_hotel_hilton_20180419b'].find({})

    # cursor = db['Task_Queue_file_downloader_TaskName_image_GT_tuniu_20180414'].find({})
    for line in cursor:
        line.pop('_id')
        line['running'] = 0
        line['finished'] = 0
        line['used_times'] = 0
        line['worker'] = 'proj.total_tasks.hilton_detail_task'
        collections.replace_one({'source_id': line['args']['source_id']}, replacement=line, upsert=True)

    #一个源一分钟500个
    insert_task('hotel_detail', limit=1000)
    # insert_task('file_downloader', limit=500)
