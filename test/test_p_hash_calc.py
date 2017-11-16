#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/1 上午11:15
# @Author  : Hou Rong
# @Site    : 
# @File    : test_p_hash_calc.py
# @Software: PyCharm
from proj.tasks import p_hash_calculate
from proj.my_lib.Common.TaskResponse import TaskResponse

if __name__ == '__main__':
    # source, bucket_name, file_name, file_md5,
    # p_hash_calculate(**{
    #     "source": "agoda",
    #     "_type": "hotel",
    #     "bucket_name": "mioji-hotel",
    #     "file_name": "96c132c46fe55602eaa2b5c0a926aaa6.jpg",
    #     "file_md5": "8eecbe0adce49423587f58c505a55382",
    #     "task_response": TaskResponse()
    # })

    p_hash_calculate(**{
        "source": "daodao",
        "_type": "poi",
        "bucket_name": "mioji-attr",
        "file_name": "5cfddb592fc0485fe39e61f5aa929b87.jpg",
        "file_md5": "3c122191721d8856ee56f1fdcfa86e6c",
        "task_response": TaskResponse()
    })
