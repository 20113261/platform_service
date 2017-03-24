# coding=utf-8
import pymysql
import zlib

CONN_DICT = {
    'host': '10.10.231.105',
    'user': 'hourong',
    'password': 'hourong',
    'charset': 'utf8',
    'db': 'FileSaver'
}


def save_file(id, task_id, content):
    conn = pymysql.connect(**CONN_DICT)
    with conn as cursor:
        data = zlib.compress(content.encode('utf8'))
        res = cursor.execute('insert into HtmlSaver VALUES (%s, %s, %s)', (id, task_id, data))
    conn.close()
    return res


def load_file_by_id(id):
    conn = pymysql.connect(**CONN_DICT)
    with conn as cursor:
        res = []
        cursor.execute('SELECT content from HtmlSaver WHERE id=%s', (id,))
        for line in cursor.fetchall():
            res.append(zlib.decompress(line[0]))
    conn.close()
    return res


def load_file_by_task_id(task_id):
    conn = pymysql.connect(**CONN_DICT)
    with conn as cursor:
        res = []
        cursor.execute('SELECT content from HtmlSaver WHERE task_id=%s', (task_id,))
        for line in cursor.fetchall():
            res.append(zlib.decompress(line[0]))
    conn.close()
    return res


if __name__ == '__main__':
    # import requests
    #
    # page = requests.get(
    #     'http://www.booking.com/hotel/it/the-lodge-aosta.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBA-gBAagCBA;sid=5875b6f83ef95de6dae9208343b10797;checkin=2017-04-03;checkout=2017-04-04;ucfs=1;soh=1;highlighted_blocks=;all_sr_blocks=;room1=A,A;soldout=0,0;hpos=9;dest_type=city;dest_id=-110502;srfid=944ba4e83083c5ab51b37424d1cee4c21ce28c1cX144;highlight_room=')
    # print save_file('test', 'test', page.text)

    print load_file_by_id('01aaf38b434b3c88aac4f6ecadea9194')[0]
