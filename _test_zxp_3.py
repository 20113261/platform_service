#coding:utf-8
# @Time    : 2018/5/22
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : _test_zxp_3.py
# @Software: PyCharm
from DBUtils.PooledDB import PooledDB
from proj.my_lib.logger import get_logger

logger = get_logger(__name__)


column = {'int': 'int', 'varchar': 'varchar', 'text': 'text'}

def init_pool(host, user, password, database, max_connections=20):
    mysql_db_pool = PooledDB(creator=pymysql, mincached=1, maxcached=2, maxconnections=max_connections,
                             host=host, port=3306, user=user, passwd=password,
                             db=database, charset='utf8mb4', blocking=True)
    return mysql_db_pool


def subtask_into_mysql(args, kwargs):
    try:
        conn_pool = init_pool(kwargs['mysql_set'])
        conn = conn_pool.connection()
        cursor = conn.cursor()
        cursor.execute(kwargs['sql'])
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.exception(msg='mysql异常', exc_info=e)
        logger.info(kwargs['sql'])


def test_insert():
    db_config = dict(
        user='mioji_admin',
        password='mioji1109',
        host='10.10.228.253',
        database='ServicePlatform'
    )
    sql = '''INSERT IGNORE INTO {} ({}, {}, {}, {}, {}) VALUES ({},{},{},{},{})'''
    subtask_into_mysql({'mysql_set': db_config})