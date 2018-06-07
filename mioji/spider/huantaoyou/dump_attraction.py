#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from mongo import get_collection
from pymongo.errors import BulkWriteError
import MySQLdb
import traceback

mysql = MySQLdb.connect(host="10.10.69.170",    # your host, usually localhost
                        user="reader",         # your username
                        passwd="miaoji1109",  # your password
                        db="base_data",
                        charset='utf8')        # name of the data base
cur = mysql.cursor()

attraction = get_collection('attraction')


sql = '''SELECT
    a.id,
    a.name,
    a.name_en,
    a.map_info,
    a.city_id,
    c.name     AS city_name,
    c.name_en  AS city_name_en,
    c.tri_code AS city_code,
    c.country_name,
    c.country_name_en,
    c.country_code,
    c.country_id
FROM chat_attraction a, (SELECT
                        city.id,
                        city.name,
                        city.name_en,
                        city.tri_code,
                        country.mid as country_id,
                        country.name    AS country_name,
                        country.name_en AS country_name_en,
                        country.country_code
                    FROM city, country
                    WHERE city.country_id = country.mid) AS c
WHERE a.city_id = c.id;'''

cur.execute(sql)


count = 0
collections = []
for row in cur.fetchall():
    tmp = {
        'id': row[0],
        'name_cn': row[1],
        'name_en': row[2],
        'coordinate': row[3],
        'city_id': row[4],
        'city_name_cn': row[5],
        'city_name_en': row[6],
        'city_code': row[7],
        'country_name_cn': row[8],
        'country_name_en': row[9],
        'country_code': row[10],
        'country_id': row[11]
    }
    collections.append(tmp)
    if len(collections) % 100 == 0:
        try:
            attraction.insert_many(collections, ordered=False)
        except BulkWriteError as bwe:
            if isinstance(bwe.details, dict):
                count += bwe.details['nInserted']
            else:
                print bwe.details

        collections = []
        print count
attraction.insert_many(collections)
print count

mysql.close()
