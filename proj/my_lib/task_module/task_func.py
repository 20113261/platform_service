import json
import hashlib
import MySQLdb


def get_task_id(worker, args):
    return hashlib.md5((worker + args).encode()).hexdigest()


def get_task(worker=None, limit=30000):
    if not worker:
        raise TypeError("No Such Worker: " + worker)
    conn = MySQLdb.connect(host='localhost', user='hourong', passwd='hourong', db='Task', charset="utf8")
    with conn as cursor:
        sql = 'select id,args,used_times from Task where finished=0 and used_times<10 and worker="{0}" order by priority desc ,update_time limit {1}'.format(
            worker, limit)
        update_sql = 'update Task set used_times=%s where id=%s'
        cursor.execute(sql)
        for line in cursor.fetchall():
            cursor.execute(update_sql, (line[2] + 1, line[0]))
            yield line[0], json.loads(line[1])
    conn.close()


def get_task_total(limit=30000):
    conn = MySQLdb.connect(host='localhost', user='hourong', passwd='hourong', db='Task', charset="utf8")
    with conn as cursor:
        sql = 'select id,args,used_times,worker from Task where finished=0 and used_times<10 order by priority desc ,update_time limit {0}'.format(
            limit)
        update_sql = 'update Task set used_times=%s where id=%s'
        cursor.execute(sql)
        for line in cursor.fetchall():
            cursor.execute(update_sql, (line[2] + 1, line[0]))
            yield line[0], json.loads(line[1]), line[3]
    conn.close()


def update_task(task_id):
    conn = MySQLdb.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='Task', charset="utf8")
    with conn as cursor:
        update_sql = 'update Task set finished=%s where id=%s'
        cursor.execute(update_sql, (1, task_id))
    conn.close()


def insert_task(data):
    conn = MySQLdb.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='Task', charset="utf8")
    sql = 'insert ignore into Task (`id`,`worker`,`args`,`priority`, `task_name`) VALUES (%s, %s, %s, 1, %s)'
    with conn as cursor:
        cursor.executemany(sql, data)
    conn.close()


if __name__ == '__main__':
    from collections import defaultdict

    _c_dict = defaultdict(int)
    for task_id, args, worker in get_task_total():
        _c_dict[worker] += 1
    print _c_dict
