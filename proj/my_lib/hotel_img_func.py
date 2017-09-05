import hashlib

import pymysql
import db_img
import datetime

from sqlalchemy import Column, String, Text, create_engine, TIMESTAMP, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = create_engine('mysql+pymysql://hourong:hourong@10.10.189.213:3306/update_img?charset=utf8',
                       encoding="utf-8", pool_size=100, pool_recycle=3600, echo=False)
DBSession = sessionmaker(bind=engine)

class PicRelation(Base):
    __tablename__ = 'pic_relation'
    source = Column(String(20), primary_key=True)
    source_id = Column(String(64), primary_key=True)
    pic_url = Column(Text())
    pic_md5 = Column(String(64))
    part = Column(String(10), primary_key=True)
    hotel_id = Column(String(20), default='')
    status = Column(String(10), default=-1)
    update_date = Column(TIMESTAMP, default=datetime.datetime.now)
    size = Column(String(40))
    flag = Column(String(10))
    file_md5 = Column(String(32), primary_key=True)

class PoiRelation(Base):
    __tablename__ = 'poi_bucket_relation'
    file_name = Column(String(100))
    source = Column(String(30))
    sid = Column(String(100), primary_key=True)
    url = Column(Text())
    pic_size = Column(String(60))
    bucket_name = Column(String(128))
    url_md5 = Column(String(1024))
    pic_md5 = Column(String(64), primary_key=True)
    use = Column(String(10))
    part = Column(String(32))
    date = Column(TIMESTAMP, default=datetime.datetime.now)

'''
| source      | varchar(20)  | NO   | PRI | NULL              |                             |
| source_id   | varchar(256) | NO   | PRI |                   |                             |
| pic_url     | text         | YES  |     | NULL              |                             |
| pic_md5     | varchar(512) | NO   |     | NULL              |                             |
| part        | varchar(10)  | YES  |     | NULL              |                             |
| hotel_id    | varchar(20)  | NO   |     | NULL              |                             |
| status      | varchar(10)  | NO   |     | -1                |                             |
| update_date | timestamp    | NO   |     | CURRENT_TIMESTAMP | on update CURRENT_TIMESTAMP |
| size        | varchar(40)  | YES  |     |                   |                             |
| flag        | varchar(10)  | YES  |     | 1                 |                             |
'''

__sql_dict = {
    'host': '10.10.189.213',
    'user': 'hourong',
    'passwd': 'hourong',
    'charset': 'utf8',
    'db': 'update_img'
}


def get_stream_md5(stream):
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: stream.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_md5(f_name):
    hash_md5 = hashlib.md5()
    with open(f_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def hotel_make_kw(args):
    relation = PicRelation()
    relation.source, relation.source_id, relation.pic_url, relation.pic_md5, relation.part, relation.size, relation.flag, relation.file_md5 = args
    insert_db(relation)

def poi_make_kw(args):
    relation = PoiRelation()
    relation.file_name, relation.source, relation.sid, relation.url, relation.pic_size, relation.bucket_name, relation.url_md5, relation.pic_md5, relation.use, relation.part = args
    insert_db(relation)


def insert_db(relation):
    dbss = DBSession()
    dbss.merge(relation)
    dbss.commit()

def insert_db_old(args):
    conn = pymysql.connect(**__sql_dict)
    with conn as cursor:
        sql = 'replace into pic_relation (`source`,`source_id`,`pic_url`,`pic_md5`,`part`,`size`,`flag`, `file_md5`) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)'
        res = cursor.execute(sql, args)
    conn.close()
    return res


def insert_too_large(args):
    conn = pymysql.connect(**__sql_dict)
    with conn as cursor:
        sql = 'insert into TooLargePic (`file_name`,`file_size`) VALUES (%s,%s)'
        res = cursor.execute(sql, args)
    conn.close()
    return res


if __name__ == '__main__':
    print get_file_md5('/search/image/hotelinfo_zls_lx20161226_img/fff91daa07bc091d791e08bcfa8a9a28.jpg')
