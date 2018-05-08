#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/22 下午3:01
# @Author  : Hou Rong
# @Site    : 
# @File    : store_utils.py
# @Software: PyCharm
import json
import types
from logger import logger
from utils import current_log_tag, get_local_ip

# 需要增加翻页信息的数据库插入方法中，当前为 guest_info 所在位置
INDEX_INFO_INDEX = {
    "InsertHotel_room3": -1,
    "InsertHotel_room4": -2
}

# 需要增加 stop by 字段的修改，此处为 stopby 所在的位置
# 字段内容： E、P、B、F，E 经济舱 P 超级经济舱 B 商务舱 F 头等舱
TICKET_INFO_INDEX = {
    "InsertNewFlight": -7,
    "InsertNewFlight3": -6,
    "InsertMultiFlight": -7,
    "InsertRoundFlight2": -9,
}


def add_index_info(versions, result, page_index):
    # 获取 guest info 所在的位置
    index_info_index = INDEX_INFO_INDEX.get(versions, None)
    if index_info_index is None:
        return

    logger.debug(
        current_log_tag() + '[修改 index_info][versions: {0}][位置 {1}]'.format(versions, index_info_index))
    for __i in range(len(result)):
        if result[__i]:
            result[__i] = list(result[__i])
            old_index_info = result[__i][index_info_index]
            try:
                old_index_info = json.loads(old_index_info)
                if not isinstance(old_index_info, types.DictType):
                    raise Exception('Type Is Not Dict')
            except Exception:
                old_index_info = {'unparse_info': old_index_info}
            index_info = {k: v for k, v in old_index_info.items()}
            index_info['page_index'] = page_index
            index_info['item_index'] = __i
            result[__i][index_info_index] = json.dumps(index_info)
            result[__i] = tuple(result[__i])


def add_stop_by_info(versions, result, task):
    # 获取 stop by info 所在的位置
    stop_by_index = TICKET_INFO_INDEX.get(versions, None)
    if stop_by_index is None:
        logger.debug('[未找到 stop_by_index][versions: {0}]'.format(versions))
        # try:
        #     from common import db
        #     sql = 'REPLACE INTO new_frame_not_replace_stop_by (ip, versions) VALUES (%s, %s)'
        #     db.execute_into_spider_db(sql, (get_local_ip(), versions))
        # except Exception as e:
        #     logger.warning('[未成功入 未找到 stop_by 库][ERROR: {0}]'.format(e))
        return

    logger.debug(
        current_log_tag() + '[修改 stop_by_info][versions: {0}][位置 {1}]'.format(versions, stop_by_index))

    for __i in range(len(result)):
        if result[__i]:
            result[__i] = list(result[__i])

            #  E、P、B、F，E 经济舱 P 超级经济舱 B 商务舱 F 头等舱
            task_stop_by_info = task.ticket_info.get('v_seat_type', None) or 'E'
            if versions == 'InsertMultiFlight':
                result[__i][stop_by_index] = '{0}&NULL'.format(task_stop_by_info)
            else:
                result[__i][stop_by_index] = task_stop_by_info

            result[__i] = tuple(result[__i])
