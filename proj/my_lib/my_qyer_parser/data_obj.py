# coding=utf-8
import datetime

from sqlalchemy import Column, String, Text, create_engine, TIMESTAMP, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Qyer(Base):
    __tablename__ = 'qyer'
    id = Column(String(32), nullable=False, primary_key=True, default='NULL')
    source = Column(String(32), nullable=False, primary_key=True, default='NULL')
    name = Column(String(256), default='NULL')
    name_en = Column(String(256), default='NULL')
    name_py = Column(String(128), default='NULL')
    alias = Column(String(256), default='NULL')
    map_info = Column(String(64), default='NULL')
    city_id = Column(String(64), default='NULL')
    source_city_id = Column(String(16), nullable=False, primary_key=True)
    source_city_name = Column(String(256), default='NULL')
    source_city_name_en = Column(String(256), default='NULL')
    source_country_id = Column(String(16), default='NULL')
    source_country_name = Column(String(256), default='NULL')
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
    url = Column(String(512), default='NULL')
    phone = Column(String(64), default='NULL')
    site = Column(String(256), default='NULL')
    imgurl = Column(String(512), default='NULL')
    commenturl = Column(String(512), default='NULL')
    introduction = Column(Text(), default='NULL')
    opentime = Column(String(1000), default='NULL')
    price = Column(String(1024), default='NULL')
    recommended_time = Column(String(1024), default='NULL')
    wayto = Column(String(1024), default='NULL')
    crawl_times = Column(Integer(), default=0)
    status = Column(Integer(), default=-1)
    insert_time = Column(TIMESTAMP, default=datetime.datetime.now)
    flag = Column(Integer(), default=0)


# 初始化数据库连接:
engine = create_engine('mysql+mysqlconnector://hourong:hourong@10.10.180.145:3306/Qyer')
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    # session = DBSession()
    # h = Hotel()
    # session.add(h)
    # session.commit()
    # session.close()
