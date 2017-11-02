#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/1 上午11:15
# @Author  : Hou Rong
# @Site    : 
# @File    : test_p_hash_calc.py
# @Software: PyCharm
from proj.tasks import p_hash_calculate
from proj.my_lib.BaseTask import TaskResponse

if __name__ == '__main__':
    # source, bucket_name, file_name, file_md5,
    p_hash_calculate(**{
        "source": "agoda",
        "_type": "hotel",
        "bucket_name": "mioji-hotel",
        "file_name": "a24af36faf3e2f67a0816e8793c89973.jpg",
        "file_md5": "2c45d422583f841fcab3daa6f2402a1e",
        "task_response": TaskResponse()
    })
