#!/usr/bin/python
# -*- coding: UTF-8 -*-
from logger import logger
import pika
import json
# 代理回调，初始化mq



class CallBack:

    def __init__(self):
        self.connection = None

    def c(self):
        print "mq 建立连接"
        credentials = pika.PlainCredentials(username="writer", password="miaoji1109")
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="10.10.160.200", port=5672, virtual_host='offline', credentials=credentials
            )
        )
        print "mq 建立连接"


    def callback(self, proxy_info,code, time_len, task):
        print "代理回调"
        try:
            
            channel = self.connection.channel()
            channel.queue_declare(queue="spiderToProxy", durable=True)
            channel.exchange_declare(exchange='spider', durable=True)
            logger.info("代理入库开始")
            proxy_info = json.loads(proxy_info[1])
            source = proxy_info['resp'][0]['source']
            external_ip = proxy_info['resp'][0]['ips'][0]['external_ip']
            inner_ip = proxy_info['resp'][0]['ips'][0]['inner_ip']

            qid = str(task.ticket_info.get('qid',0))

            args = {"source": "source",
                "external_ip": "external_ip",
                "inner_ip": "inner_ip",
                "error_code": str("code"),
                "cost": "str(int(time_len))",
                "qid": "qid",}
            msg = json.dumps({"callback": args}, ensure_ascii=True)
            logger.info("mq入库信息：{0}".format(msg))
            res = channel.basic_publish(exchange='spider', routing_key="spider_proxy", body=msg, properties=pika.BasicProperties(
                                            delivery_mode=2))
            logger.info("mq入库成功")

        except Exception as e:
            logger.debug("代理服务mq回调入库失败：{0}".format(e))
            self.c()


    def proxy_rabbitmq_close(self,):
        self.connection.close()
    