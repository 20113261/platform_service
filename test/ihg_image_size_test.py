#coding:utf-8
import datetime
import pymongo
'''
修改ihg的图片大小，去掉url的后缀
'''
client = pymongo.MongoClient(host='10.10.231.105')
# collections = client['MongoTask']['Task_Queue_file_downloader_TaskName_images_hotel_ihg_20171220a']

# cursor = collections.find({}).limit(29167)
# id_list = (id_dict['_id'] for id_dict in cursor)
# # print(len(id_list))
# for id in id_list:
#     url = collections.find_one({"_id": id}, {"args": 1})['args']['target_url']
#     url = url.replace('&wid=80&hei=80', '')
#     print url
#     result = collections.update({
#         '_id': id
#     }, {
#         '$set': {
#             'args.target_url': url,
#             'finished': 0,
#             'used_times': 0,
#             'running': 0
#         }
#     }, multi=True)
#     print(result)

collections = client['MongoTask']['Task_Queue_hotel_detail_TaskName_detail_hotel_marriott_20170109a']
cursor = collections.find({"args.url":{"$regex":"www\.(?!marriott)"}}, {"_id":1,"args.url":1}).limit(100)
id_list = [id_dict['_id'] for id_dict in cursor]
print len(id_list)
print cursor
for id in id_list:
    url = collections.find_one({"_id": id})['args']['url']
    print url