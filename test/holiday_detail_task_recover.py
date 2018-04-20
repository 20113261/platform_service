from sqlalchemy.engine import create_engine
import MySQLdb
import pymongo


client = pymongo.MongoClient('10.10.231.105', 27017)
collections = client['MongoTask']['Task_Queue_hotel_detail_TaskName_detail_hotel_holiday_20171226a']

conn = MySQLdb.connect(host='10.10.228.253',
        port = 3306,
        user='mioji_admin',
        passwd='mioji1109',
        db ='ServicePlatform',)

cur = conn.cursor()
result = cur.execute("select * from list_hotel_holiday_20171226a")
print result
hotel = {}
for record in cur.fetchall():
    hotel_name = record[1]
    hotel[hotel_name] = record[4]
    # print record

mongo_cursor = collections.find({})

detail_set = set()
diff_result = {}

for i in mongo_cursor:
    # print i["args"]["source_id"]
    detail_set.add(i["args"]["source_id"])

print len(detail_set)

for key, value in hotel.items():
    if key not in detail_set:
        print key
        diff_result[key] = value
print diff_result
print len(diff_result)
