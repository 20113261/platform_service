#coding:utf-8
import pymongo

client = pymongo.MongoClient('10.10.231.105', 27017)
collections = client['MongoTask']['Task_Queue_hotel_list_TaskName_tax_total_hilton_20180107b']

client_final = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')

collections_final = client_final['data_result']['hilton_20180107']

print collections_final

cursor = collections.find({})
cursor_final = collections_final.find({})
# print len(id_list)
success_result = dict()
for i in cursor_final:
    # print i
    result = i['result']
    # print i['task_id'], len(result)
    # try:
    if len(result):
        hotel_id = result[0][3]
        check_in = i['check_in']
        hotel = hotel_id + '_' + check_in
        success_result[hotel] = len(result)

print len(success_result)
fail_result = []
task_list = []
for i in cursor:
    # print i
    hotel = i['args']['source_id'] + '_' + i['args']['check_in']
    task_list.append(hotel)
    if hotel not in success_result:
        # print hotel
        fail_result.append(hotel)
print len(fail_result)

for key, value in success_result.items():
    print key
    if key not in task_list:
        print key