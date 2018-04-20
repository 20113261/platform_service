#coding:utf-8
from my_logger import get_logger
# from MongoTask.MongoTaskInsert import InsertTask
import pymongo
import pymysql
from DBUtils.PooledDB import PooledDB
from collections import defaultdict
import re
import mock
import patched_mongo_insert

logger = get_logger("test_count")




class TestCount(object):
    def __init__(self, db_name, coll_name):
        self.logger = get_logger("test_count")
        self.tasks = []
        client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
        self.collections = client[db_name][coll_name]
        self.create_index()
        # 数据游标偏移量，用于在查询时发生异常恢复游标位置
        self.offset = 0
        # 数据游标前置偏移量，用于在入库时恢复游标位置
        self.pre_offset = 0

    def create_index(self):
        self.collections.create_index([('pid', 1), ('url', 1)])

    def mongo_patched_insert(self):
        with mock.patch('pymongo.collection.Collection._insert', patched_mongo_insert.Collection._insert):
            result = self.collections.insert(self.tasks, continue_on_error=True)
            return result

    def insert_mongo(self):
        if len(self.tasks) > 0:
            res = self.mongo_patched_insert()
            self.logger.info("[update offset][offset: {}][pre offset: {}]".format(self.offset, self.pre_offset))
            self.offset = self.pre_offset
            self.logger.info("[insert info][ offset: {} ][ {} ]".format(self.offset, res))
            self.logger.info('[ 本次准备入库任务数：{0} ][ 实际入库数：{1} ][ 库中已有任务：{2} ][ 已完成总数：{3} ]'.format(
                self.tasks.__len__(), res['n'], res.get('err', 0), self.offset))
            self.tasks = []

    def insert_task(self):
        if len(self.tasks) >= 2000:
            self.insert_mongo()

    def test_count(self):
        for pid, url in self.get_GT_tasks():
            self.tasks.append({"pid": pid, "url": url})
            self.pre_offset += 1
        self.insert_mongo()

    def get_GT_tasks(self):
        # sql = '''SELECT sid, url FROM img_list;'''
        # for line in fetchall(spider_base_tmp_wanle_pool, sql, is_dict=True):
        #     yield line['sid'], line['url']
        client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
        collections = client['data_result']['tuniuGT_detail']
        # collections = client['data_result']['tuniuGT_detail']
        se = defaultdict(set)
        j = 0
        for co in collections.find({}):
            j += 1
            print(j)
            try:
                pid = co['args']['id']
            except Exception as e:
                print(co)
            for c in co['result']:
                pro = len(se[pid])
                se[pid].add(c['first_image'])
                if pro < len(se[pid]):
                    yield pid, c['first_image']

                for i in c['image_list']:
                    pro = len(se[pid])
                    se[pid].add(i)
                    if pro < len(se[pid]):
                        yield pid, i

                for i in c['route_day']:
                    for ii in i['detail']:
                        for iii in ii['image_list']:
                            pro = len(se[pid])
                            se[pid].add(iii)
                            if pro < len(se[pid]):
                                yield pid, iii

                for i in c['hotel']['plans']:
                    pro = len(se[pid])
                    for img in i['img']:
                        se[pid].add(img)
                        if pro < len(se[pid]):
                            yield pid, i['img']


if __name__ == '__main__':
    t = TestCount('data_result', 'tuniuGT_unique_image')
    t.test_count()