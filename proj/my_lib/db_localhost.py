# coding=utf-8
import datetime

import sys
from sqlalchemy import Column, String, Text, create_engine, TIMESTAMP, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from proj.my_lib.logger import get_logger

Base = declarative_base()


# import pymysql

class Attr(Base):
    __tablename__ = 'attr'
    id = Column(String(32), nullable=False, primary_key=True)
    source = Column(String(32), nullable=False, primary_key=True, default='NULL')
    name = Column(String(256), default='NULL')
    name_en = Column(String(256), default='NULL')
    alias = Column(String(256), default='NULL')
    map_info = Column(String(64), default='NULL')
    city_id = Column(String(64), nullable=False, primary_key=True)
    source_city_id = Column(String(16), default='NULL')
    address = Column(String(512), default='NULL')
    star = Column(Float(), default=-1)
    recommend_lv = Column(String(100), default='NULL')
    pv = Column(Integer(), default=-1)
    plantocounts = Column(Integer(), default=-1)
    beentocounts = Column(Integer(), default=-1)
    overall_rank = Column(Integer(), default=-1)
    ranking = Column(String(11), default='NULL')
    grade = Column(String(11), default='NULL')
    grade_distrib = Column(String(512), default='NULL')
    commentcounts = Column(Integer(), default=-1)
    tips = Column(Text(), default='NULL')
    tagid = Column(String(256), default='NULL')
    related_pois = Column(String(256), default='NULL')
    nomissed = Column(String(1024), default='NULL')
    keyword = Column(String(512), default='NULL')
    cateid = Column(String(128), default='NULL')
    url = Column(String(320), nullable=False)
    phone = Column(String(64), default='NULL')
    site = Column(String(320), index=True, default='NULL')
    imgurl = Column(Text(), default='NULL')
    commenturl = Column(String(512), default='NULL')
    introduction = Column(Text(), default='NULL')
    first_review_id = Column(Text(), default='NULL')
    opentime = Column(String(1000), default='NULL')
    price = Column(String(1024), default='NULL')
    recommended_time = Column(String(1024), default='NULL')
    wayto = Column(String(1024), default='NULL')
    prize = Column(Integer(), default=0)
    traveler_choice = Column(Integer(), default=0)
    insert_time = Column(TIMESTAMP, default=datetime.datetime.now)


class Shop(Base):
    __tablename__ = 'shop'
    id = Column(String(32), nullable=False, primary_key=True)
    source = Column(String(32), nullable=False, primary_key=True, default='NULL')
    name = Column(String(256), default='NULL')
    name_en = Column(String(256), default='NULL')
    alias = Column(String(256), default='NULL')
    map_info = Column(String(64), default='NULL')
    city_id = Column(String(64), nullable=False, primary_key=True)
    source_city_id = Column(String(16), default='NULL')
    address = Column(String(128), default='NULL')
    star = Column(Float(), default=-1)
    recommend_lv = Column(String(100), default='NULL')
    pv = Column(Integer(), default=-1)
    plantocounts = Column(Integer(), default=-1)
    beentocounts = Column(Integer(), default=-1)
    overall_rank = Column(Integer(), default=-1)
    ranking = Column(String(11), default='NULL')
    grade = Column(String(11), default='NULL')
    grade_distrib = Column(String(512), default='NULL')
    commentcounts = Column(Integer(), default=-1)
    tips = Column(Text(), default='NULL')
    tagid = Column(String(256), default='NULL')
    related_pois = Column(String(256), default='NULL')
    nomissed = Column(String(1024), default='NULL')
    keyword = Column(String(512), default='NULL')
    cateid = Column(String(128), default='NULL')
    url = Column(String(320), nullable=False)
    phone = Column(String(64), default='NULL')
    site = Column(String(320), index=True, default='NULL')
    imgurl = Column(Text(), default='NULL')
    commenturl = Column(String(512), default='NULL')
    introduction = Column(Text(), default='NULL')
    first_review_id = Column(Text(), default='NULL')
    opentime = Column(String(1000), default='NULL')
    price = Column(String(1024), default='NULL')
    recommended_time = Column(String(1024), default='NULL')
    wayto = Column(String(1024), default='NULL')
    prize = Column(Integer(), default=0)
    traveler_choice = Column(Integer(), default=0)
    insert_time = Column(TIMESTAMP, default=datetime.datetime.now)


class Rest(Base):
    __tablename__ = 'rest'
    id = Column(String(32), nullable=False, primary_key=True)
    source = Column(String(32), nullable=False, primary_key=True, default='NULL')
    name = Column(String(256), default='NULL')
    name_en = Column(String(256), default='NULL')
    map_info = Column(String(64), default='NULL')
    city_id = Column(String(64), nullable=False, primary_key=True)
    source_city_id = Column(String(16), default='NULL')
    address = Column(String(128), default='NULL')
    ranking = Column(String(11), default='NULL')
    grade = Column(String(11), default='NULL')
    commentcounts = Column(Integer(), default=-1)
    cuisines = Column(String(256), default='NULL')
    dining_options = Column(String(1024), default='NULL')
    payment = Column(String(256), default='NULL')
    service = Column(String(1024), default='NULL')
    level = Column(Integer(), default=-1)
    michelin_star = Column(Float(), default=-1)
    recommend = Column(String(64), default='NULL')
    rating_by_category = Column(String(32), default='NULL')
    menu = Column(Text(), default='NULL')
    status = Column(Integer(), default=0)
    flag = Column(Integer(), default=0)
    url = Column(String(320), nullable=False)
    phone = Column(String(64), default='NULL')
    site = Column(String(320), index=True, default='NULL')
    imgurl = Column(Text(), default='NULL')
    commenturl = Column(String(512), default='NULL')
    introduction = Column(Text(), default='NULL')
    first_review_id = Column(Text(), default='NULL')
    opentime = Column(String(1000), default='NULL')
    price = Column(String(1024), default='NULL')
    price_level = Column(String(32), default='NULL')
    prize = Column(Integer(), default=0)
    traveler_choice = Column(Integer(), default=0)
    insert_time = Column(TIMESTAMP, default=datetime.datetime.now)


class ShortComment(Base):
    __tablename__ = 'tp_comment_0814'
    source = Column(String(128), nullable=False, default='NULL')
    city = Column(String(256))
    source_city_id = Column(String(54), primary_key=True)
    source_id = Column(String(128), default='NULL', primary_key=True)
    name = Column(String(256), default=' ')
    review_id = Column(String(54), primary_key=True)
    review_title = Column(String(1024))
    review_text = Column(Text(), nullable=False, default='NULL')
    review_link = Column(String(512))
    comment_time = Column(String(54))
    comment_rating = Column(Float(), default=-1)
    user_id = Column(String(54))
    user_name = Column(String(54))
    user_rating = Column(Float(), default=-1)
    user_link = Column(String(512))
    likes = Column(Integer(), default=-1)
    review_from = Column(String(256), index=True, default='NULL')
    language = Column(String(64), primary_key=True)
    insert_time = Column(TIMESTAMP, default=datetime.datetime.now)
    miaoji_id = Column(String(32), primary_key=True)


# class Rest(Base):
#     __tablename__ = 'rest'
#     id = Column(String(64), nullable=False, primary_key=True)
#     source = Column(String(16), nullable=False, primary_key=True, default='NULL')
#     name = Column(String(128), nullable=False)
#     name_en = Column(String(128), nullable=False)
#     map_info = Column(String(64), nullable=False)
#     city_id = Column(String(64), nullable=False, primary_key=True)
#     source_city_id = Column(String(128), default='NULL')
#     address = Column(Text(), default='NULL')
#     pv = Column(Integer(), default=-1)
#     plantocounts = Column(Integer(), default=-1)
#     beentocounts = Column(Integer(), default=-1)
#     overall_rank = Column(Integer(), default=-1)
#     ranking = Column(String(11), default='NULL')
#     grade = Column(String(11), default='NULL')
#     grade_distrib = Column(String(512), default='NULL')
#     commentcounts = Column(Integer(), default=-1)
#     tips = Column(Text(), default='NULL')
#     tagid = Column(String(256), default='NULL')
#     related_pois = Column(String(256), default='NULL')
#     nomissed = Column(String(1024), default='NULL')
#     keyword = Column(String(512), default='NULL')
#     cateid = Column(String(128), default='NULL')
#     url = Column(String(320), nullable=False)
#     phone = Column(String(64), default='NULL')
#     site = Column(String(320), index=True, default='NULL')
#     imgurl = Column(Text(), default='NULL')
#     commenturl = Column(String(512), default='NULL')
#     introduction = Column(Text(), default='NULL')
#     first_review_id = Column(Text(), default='NULL')
#     opentime = Column(String(1000), default='NULL')
#     price = Column(String(1024), default='NULL')
#     recommended_time = Column(String(1024), default='NULL')
#     wayto = Column(String(1024), default='NULL')
#     prize = Column(Integer(), default=0)
#     traveler_choice = Column(Integer(), default=0)
#     insert_time = Column(TIMESTAMP, default=datetime.datetime.now)
# 初始化数据库连接:
# engine = create_engine('mysql+pymysql://hourong:hourong@10.10.180.145:3306/Qyer')
engine = create_engine('mysql+pymysql://mioji_admin:mioji1109@10.10.228.253:3306/ServicePlatform?charset=utf8',
                       encoding="utf-8", pool_size=5, pool_recycle=3600, echo=False)
engine_mb4 = create_engine('mysql+pymysql://mioji_admin:mioji1109@10.10.228.253:3306/ServicePlatform?charset=utf8mb4',
                           encoding="utf-8", pool_size=5, pool_recycle=3600, echo=False)
# 创建DBSession类型:

DBSession = sessionmaker(bind=engine)
DBSession_mb4 = sessionmaker(bind=engine_mb4)

logger = get_logger("ImgList")


def insert(table, **kwargs):
    logger.info('------------4--------      ' + str(kwargs))
    content = {'attr': Attr, 'shop': Shop, 'rest': Rest, }[table](**kwargs)
    ss = DBSession()
    ss.merge(content)
    ss.commit()


def insert_mb4(table, **kwargs):
    content = {'tp_comment_0814': ShortComment, }[table](**kwargs)
    ss = DBSession_mb4()
    ss.merge(content)
    ss.commit()


if __name__ == '__main__':
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    # insert(id=123,source='dd',city_id='b69',url='http://www.com')
    print dir(engine)
