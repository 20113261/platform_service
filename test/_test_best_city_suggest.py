#coding:utf-8
import pymongo
import pymysql
import sys
sys.path.insert(0, '/home/luwn/zhangxiaopeng/serviceplatform')

from rabbitmq_watcher import insert_task
from proj.mysql_pool import service_platform_pool




def create_bestwest_20180421():
    client = pymongo.MongoClient(host='10.10.213.148')
    db = client['CitySuggest']
    collections_from = db['bestwest_city_suggest_20180328']
    collections = db['bestwest_city_suggest_20180421']
    collections.create_index([('id', 1), ('description', 1), ('place_id', 1)], unique=True, background=True)
    try:
        j = 0
        for i in collections_from.find({}):
            if isinstance(i['suggest'], list):
                id = i['suggest'][-1]['id']
                description = i['suggest'][-1]['description']
                place_id = i['suggest'][-1]['place_id']
                collections.find_one_and_update({'id': id, 'description':description, 'place_id': place_id}, {'$inc':{'count':1}}, upsert=True)
                j += 1
                print j
    except Exception as e:
        print(i)
        print('*'*10)


def create_bestwest_mongotask_20180423():
    client_from = pymongo.MongoClient(host='10.10.231.105')
    db_from = client_from['MongoTask']
    collections_from = db_from['Task_Queue_hotel_list_TaskName_list_hotel_bestwest_20180423a']
    client_to = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
    db_to = client_to['MongoTask_Zxp']
    collections = db_to['Task_Queue_hotel_list_TaskName_list_hotel_bestwest_20180423a']
    collections.create_index()

    for line in collections_from.find({'finished':0}):
        collections.insert(line)

if __name__ == '__main__':
    create_bestwest_20180421()