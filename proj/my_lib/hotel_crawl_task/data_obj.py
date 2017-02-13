# coding=utf-8
import datetime

from sqlalchemy import Column, String, create_engine, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class HotelCrawl(Base):
    __tablename__ = 'hotelinfo_crawl_test'
    source = Column(String(64), default='NULL', primary_key=True)
    source_id = Column(String(128), default='NULL', primary_key=True)
    city_id = Column(String(11), default='NULL', primary_key=True)
    hotel_url = Column(String(1024), default='NULL')
    flag = Column(String(40), default='NULL')
    update_time = Column(TIMESTAMP, default=datetime.datetime.now)


class Task(object):
    city_id = ''
    content = ''
    check_in = ''
    check_out = ''
    flag = ''

    def __repr__(self):
        return '<Task city_id={0}, check_in={1}, check_out={2}, content={3}, flag={4}>'.format(self.city_id,
                                                                                               self.check_in,
                                                                                               self.check_out,
                                                                                               self.content,
                                                                                               self.flag)


# 初始化数据库连接:
engine = create_engine('mysql+mysqlconnector://hourong:hourong@localhost:3306/test')
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    # session = DBSession()
    # h = Hotel()
    # session.add(h)
    # session.commit()
    # session.close()
