#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/12 下午7:56
# @Author  : Hou Rong
# @Site    : 
# @File    : KsMoveSDK.py
# @Software: PyCharm
from StringIO import StringIO
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.logger import get_logger
from proj.my_lib.ks_upload_file_stream import upload_ks_file_stream, download_content

logger = get_logger("KsMove")


class KsMoveSDK(BaseSDK):
    def get_task_finished_code(self):
        return [0, 29]

    def _execute(self, **kwargs):
        from_bucket = self.task.kwargs['from_bucket']
        to_bucket = self.task.kwargs['to_bucket']
        file_name = self.task.kwargs['file_name']
        content, md5 = download_content(
            bucket_name=from_bucket,
            file_name=file_name,
            need_md5=True
        )
        if content is not None:
            string_io = StringIO(content)
            string_io.seek(0)
            result = upload_ks_file_stream(
                bucket_name=to_bucket,
                upload_key=file_name,
                file_obj=string_io,
                hash_check=md5
            )

            if result:
                self.task.error_code = 0
            else:
                self.task.error_code = 108
        else:
            self.task.error_code = 29
        return "[finished: {}]".format(md5)
