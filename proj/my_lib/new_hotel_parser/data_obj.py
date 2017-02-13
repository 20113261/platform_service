# coding=utf-8
import datetime

from sqlalchemy import Column, String, Text, create_engine, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Hotel(Base):
    __tablename__ = 'hotelinfo_static_data'
    hotel_name = Column(String(512), default='NULL')
    hotel_name_en = Column(String(512), default='NULL')
    source = Column(String(64), default='NULL', primary_key=True)
    source_id = Column(String(128), default='NULL', primary_key=True)
    brand_name = Column(String(512), default='NULL')
    map_info = Column(String(512), default='NULL')
    address = Column(String(512), default='NULL')
    city = Column(String(512), default='NULL')
    country = Column(String(512), default='NULL')
    city_id = Column(String(11), default='NULL', primary_key=True)
    postal_code = Column(String(512), default='NULL')
    star = Column(String(20), default='-1.0')
    grade = Column(String(256), default='NULL')
    review_num = Column(String(20), default='NULL')
    has_wifi = Column(String(20), default='NULL')
    is_wifi_free = Column(String(20), default='NULL')
    has_parking = Column(String(20), default='NULL')
    is_parking_free = Column(String(20), default='NULL')
    service = Column(Text(), default='NULL')
    img_items = Column(Text(), default='NULL')
    description = Column(Text(), default='NULL')
    accepted_cards = Column(String(512), default='NULL')
    check_in_time = Column(String(128), default='NULL')
    check_out_time = Column(String(128), default='NULL')
    hotel_url = Column(String(1024), default='NULL')
    continent = Column(String(96), default='NULL', primary_key=True)
    update_time = Column(TIMESTAMP, default=datetime.datetime.now)


# 初始化数据库连接:
engine = create_engine('mysql+mysqlconnector://hourong:hourong@10.10.180.145:3306/hotel_adding')
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    # session = DBSession()
    # h = Hotel()
    # session.add(h)
    # session.commit()
    # session.close()
