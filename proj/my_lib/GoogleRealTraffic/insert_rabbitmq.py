#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/1/25 下午3:40
# @Author  : Hou Rong
# @Site    : 
# @File    : insert_rabbitmq.py
# @Software: PyCharm
import gevent.monkey

gevent.monkey.patch_all()
import pika
import json
import logging
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.Utils import retry

logger = get_logger("insert_rabbitmq")

# test
HOST = '10.10.189.213'
USER = 'hourong'
PASSWD = '1220'
EXCHANGE = 'GoogleDrive'
ROUTINE_KEY = 'GoogleDrive'
V_HOST = 'GoogleDrive'
QueueName = 'GoogleDrive'

logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger("pika").propagate = False


# online
# HOST = '10.10.38.166'
# USER = 'master'
# PASSWD = 'master'

@retry(times=3, raise_exc=True)
def insert_rabbitmq(args):
    logger.debug('[rabbitmq 入库开始]')
    try:
        credentials = pika.PlainCredentials(username=USER, password=PASSWD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=HOST, virtual_host=V_HOST, credentials=credentials
            )
        )
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE,
                                 # exchange_type='fanout',
                                 durable=True,
                                 auto_delete=False)

        # 此部分代码会修改 exchange 以及定义 queue
        channel.queue_declare(queue=QueueName, durable=True)
        channel.queue_bind(queue=QueueName, exchange=EXCHANGE, routing_key=ROUTINE_KEY)

        msg = json.dumps(args, ensure_ascii=False)

        res = channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTINE_KEY, body=msg,
                                    properties=pika.BasicProperties(
                                        delivery_mode=2))
        connection.close()
        if not res:
            raise Exception('RabbitMQ Result False')
        logger.debug('[rabbitmq 入库结束]')

    except Exception as exc:
        raise exc


if __name__ == '__main__':
    a = [(1, 2, 3), (2, 3, 4)]
    for i in range(100):
        insert_rabbitmq(args=a)
