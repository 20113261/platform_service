#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月20日

@author: dujun
'''

from mioji.common.mioji_db import new_spider_db

INSERT_SQL = '''insert INTO `hotel_suggestions_city`(city_id, source, suggestions ,select_index, annotation, error, label_batch)''' + \
             ''' VALUES (%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE suggestions=VALUES(suggestions),select_index=VALUES(select_index)''' + \
             ''',annotation=VALUES(annotation),error=VALUES(error),label_batch=VALUES(label_batch)'''

ALL_SQL = 'select * from hotel_suggestions_city where source=%s'


def store_suggests_bb(rows):
    """
    city_id,source,suggestions, select, annotation, error
    """

    with new_spider_db as connect:
        with connect as cursor:
            for r in rows:
                print 'insert', r
                cursor.execute(INSERT_SQL, r)


def store_suggests(rows):
    """
    city_id,source,suggestions, select, annotation, error
    """
    connect = new_spider_db.open()
    cursor = connect.cursor()
    cursor.executemany(INSERT_SQL, rows)
    connect.commit()
    new_spider_db.close()


def sotre_ss(r):
    connect = new_spider_db.open()
    cursor = connect.cursor()
    print 'rowww', r
    cursor.execute(INSERT_SQL, r)
    connect.commit()
    new_spider_db.close()


def cut(rows, size=500):
    cut_list = []
    all_c = len(rows)
    offest = 0
    while offest < all_c:
        cut_list.append(rows[offest:offest + size])
        offest += size

    return cut_list


def find_suggest(source, city_id):
    with new_spider_db as connect:
        with connect as cursor:
            cursor.execute('select * from hotel_suggestions_city where source=%s and city_id=%s', (source, city_id))
            res = cursor.fetchall()
    if res:
        return res[0]
    else:
        return None


def find_suggests(source, page, page_size=500, annotation=-1):
    with new_spider_db as connect:
        with connect as cursor:
            if annotation != -1:
                cursor.execute(ALL_SQL + ' and annotation=%s limit %s,%s',
                               (source, annotation, (page - 1) * page_size, page_size))
            else:
                cursor.execute(ALL_SQL + ' limit %s,%s', (source, (page - 1) * page_size, page_size))
            all_ = cursor.fetchall()
            return all_


def update_suggests(city_id, source, suggestions=None, select_index=-1, annotation=-1, error=None):
    set_clo = []
    values = []
    if suggestions:
        set_clo.append('suggestions=%s')
        values.append(suggestions)
    if select_index != -1:
        set_clo.append('select_index=%s')
        values.append(select_index)
    if annotation != -1:
        set_clo.append('annotation=%s')
        values.append(annotation)
    if error:
        set_clo.append('error=%s')
        values.append(error)

    if not set_clo:
        return

    set_sql = 'SET ' + ','.join(set_clo)
    values.append(city_id)
    values.append(source)

    with new_spider_db as connect:
        with connect as cursor:
            print 'UPDATE hotel_suggestions_city ' + set_sql + ' where city_id=%s and source=%s', values
            print cursor.execute('UPDATE hotel_suggestions_city ' + set_sql + ' where city_id=%s and source=%s', values)


def get_empty_suggest(source):
    with new_spider_db as connect:
        with connect as cursor:
            cursor.execute("select city_id from hotel_suggestions_city where source=%s and suggestions='[]'", (source,))
            res = cursor.fetchall()
            return [r[0] for r in res]


def get_annotation_suggest(source, annotation=-1):
    """
    -1 不指定；-100 重复；1 精确匹配；2 。。。
    """
    with new_spider_db as connect:
        with connect as cursor:
            if annotation != -1:
                cursor.execute(ALL_SQL + ' and annotation=%s', (source, annotation))
            else:
                cursor.execute(ALL_SQL, (source,))
            res = cursor.fetchall()
            return res


def get_label_suggest(source):
    with new_spider_db as connect:
        with connect as cursor:
            cursor.execute(ALL_SQL + ' and select_index > 0', (source,))
            res = cursor.fetchall()
            return res


if __name__ == '__main__':
    #     update_suggests(1, 'booking', error='{code:1}')
    #     print find_suggests('booking', 1)
    rows = get_label_suggest('booking', 0)
    ids = [r[1] for r in rows]
