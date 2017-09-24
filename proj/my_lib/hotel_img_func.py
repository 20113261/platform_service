import hashlib

import pymysql
import db_img
import datetime

from sqlalchemy import Column, String, Text, create_engine, TIMESTAMP, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

# from proj.my_lib.logger import get_logger
# logger = get_logger('imgmd5_primary_key')

Base = declarative_base()

engine = create_engine('mysql+pymysql://hourong:hourong@10.10.189.213:3306/update_img?charset=utf8',
                       encoding="utf-8", pool_size=100, pool_recycle=3600, echo=False)
DBSession = sessionmaker(bind=engine)
SQL_HOTEL = 'replace into {table_name} (source, source_id, pic_url, pic_md5, part, hotel_id, status, update_date, size, flag, file_md5) values (:source, :source_id, :pic_url, :pic_md5, :part, :hotel_id, :status, :update_date, :size, :flag, :file_md5)'
SQL_POI = 'replace into {table_name} (file_name, source, sid, url, pic_size, bucket_name, url_md5, pic_md5, use, part, date) values (:file_name, :source, :sid, :url, :pic_size, :bucket_name, :url_md5, :pic_md5, :use, :part, :date)'

class PicRelation(Base):
    __tablename__ = 'pic_relation_0905'
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
    __tablename__ = 'poi_bucket_relation_0925'
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
    relation.source, relation.source_id, relation.pic_url, relation.pic_md5, relation.part, relation.size, relation.flag, relation.file_md5, _temp = args
    relation.hotel_id = ''
    relation.status = -1
    relation.update_date = datetime.datetime.now()
    sql = SQL_HOTEL.format(table_name=relation.__tablename__)

    # logger.info(relation.source+'|'+ relation.source_id+'|'+relation.part+'|'+relation.file_md5+'|'+relation.pic_md5)
    insert_db(sql, relation)

def poi_make_kw(args):
    relation = PoiRelation()
    relation.source, relation.sid, relation.url, relation.file_name, relation.part, relation.size, relation.use, relation.pic_md5, relation.bucket_name = args
    relation.date = datetime.datetime.now()
    relation.url_md5 = relation.file_name.split('.')[0]
    sql = SQL_POI.format(table_name=relation.__tablename__)
    insert_db(sql, relation)


def insert_db(sql, relation):
    dbss = DBSession()
    dbss.execute(text(sql), [relation.__dict__])
    dbss.commit()

def insert_db_old(args):
    conn = pymysql.connect(**__sql_dict)
    with conn as cursor:
        sql = 'replace into pic_relation_0914 (`source`,`source_id`,`pic_url`,`pic_md5`,`part`,`size`,`flag`, `file_md5`) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)'
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
    # print get_file_md5('/search/image/hotelinfo_zls_lx20161226_img/fff91daa07bc091d791e08bcfa8a9a28.jpg')
    aa = {'status': -1,
          'update_date': datetime.datetime(2017, 9, 5, 16, 18, 30, 445896),
          'hotel_id': '',
          'file_md5': 'd41d8cd98f00b204e9800998ecf8427e',
          'source': u'hotels',
          'flag': 0,
          'part': u'44',
          'pic_md5': u'4fef069236f03ec10a97fa84deeeefa4.jpg',
          'source_id': u'418161',
          'pic_url': u'https://exp.cdn-hotels.com/hotels/6000000/5390000/5388400/5388301/5388301_2_y.jpg',
          'size': '(334, 500)'}
    args = ('hotels', '418161', 'https://exp.cdn-hotels.com/hotels/6000000/5390000/5388400/5388301/5388301_2_y.jpg',
            '4fef069236f03ec10a97fa84deeeefa4.jpg', '44', '(334, 500)', 0, 'd41d8cd98f00b204e9800998ecf8427e', )
    hotel_make_kw(args)