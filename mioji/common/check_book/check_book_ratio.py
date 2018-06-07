# encoding: utf-8
import mysql_ext
from datetime import datetime as dt
from check_book_config import check_book_ratio_development
from check_book_config import check_book_ratio_online
from check_book_config import check_book_ratio_test
import time
import json
from mioji.common import parser_except
from mioji.common.logger import logger
__auth__ = 'fan bowen'


# 本文件是为了满足查定比的需求


class CheckBookRatio(object):
    # 此类为了查询sql用的
    def __init__(self, **kwargs):
        self.task = kwargs.get("task")
        ticket_info = self.task.ticket_info
        other_info = self.task.other_info
        self.type_info = ticket_info.get("env_name", "NULL")
        self._mysql = mysql_ext.MySQLExt(**check_book_ratio_test)
        if self.type_info == "online":
            self._mysql = mysql_ext.MySQLExt(**check_book_ratio_online)
        print kwargs       
        self.api_name = kwargs.get('api_name')  # 更新以qid为单条记录     
        self.unionKey = kwargs.get('unionKey', '')  # 源id

        self.table = 'checkbook_statistic_partner_source'
        self.record_table = 'checkbook_partner_source'

        self.ptid = other_info.get('ptid', '')  # 企业id
        self.today = dt.today().strftime("%Y%m")
        self.acc = other_info.get('api_acc', '')  # 账号模式
        if self.acc is None:
            # 这个字段会有两个样式。很气~
            self.acc = other_info.get('apiAcc', '')
        # self.method = kwargs.get('method', '')  # 这个参数是说明更新哪个字段的
        try:
            auth_acc_id = json.loads(ticket_info["auth"])['acc_mj_uid']
        except:
            auth_acc_id= "test"
            logger.error("未传入acc_mj_uid，暂为测试做try")
        self.acc_id = auth_acc_id #具体账号的id

        self.qid = ticket_info.get('qid')
        self.record_tuple = kwargs.get('record_tuple')  # 此处tuple形如为(1, 2, 3) 为此qid 使用了一次查询数 两笔订单数 三次退单数
        self.citme = int(time.time())

    def insert_record_qid(self):
        try:
            
            sql = "INSERT INTO checkbook_partner_source values('{ptid}', '{unionKey}', {ctime}, {acc}, '{acc_id}', '{api}', {qid}, {check}, " \
                    "{book}, {refund});".format(ptid=self.ptid, unionKey=self.unionKey, ctime=self.citme, acc=self.acc, acc_id=self.acc_id,
                                               qid=self.qid,
                                               api=self.api_name, check=self.record_tuple[0],
                                               book=self.record_tuple[1], refund=self.record_tuple[2])
            logger.info("[插入查定比][sql][{0}]".format(sql))
            self._mysql.exec_sql(sql)
        except Exception as why:
            logger.info("[插入查定比记录失败]：{0}".format(why))
            
        finally:
            self._mysql.close()

def use_record_qid(**kwargs):
    _record = CheckBookRatio(**kwargs)
    _record.insert_record_qid()

if __name__ == "__main__":
    # use_check(ptid='A66691', unionKey='s119', acc=1, type_info="test")
    # use_book(ptid='A66691', unionKey='s119', acc=1)
    # use_cancel(ptid='A66691', unionKey='s119', acc=1)
    use_record_qid(ptid='A66691', unionKey='s119', acc=1, api_name="JAC", qid="15802436213", record_tuple=[3, 1, 0], type_info="test")



