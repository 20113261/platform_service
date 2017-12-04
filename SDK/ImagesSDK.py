#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/16 下午7:07
# @Author  : Hou Rong
# @Site    : ${SITE}
# @File    : ImagesSDK.py
# @Software: PyCharm
import hashlib
import json
from StringIO import StringIO

from sqlalchemy import exc

from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.img_hash import img_p_hash
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.hotel_img_func import get_stream_md5, poi_make_kw, hotel_make_kw
from proj.my_lib.is_complete_scale_ok import is_complete_scale_ok
from proj.my_lib.ks_upload_file_stream import upload_ks_file_stream
from proj.my_lib.logger import func_time_logger


class ImagesSDK(BaseSDK):
    def _execute(self, **kwargs):
        # init task val
        source = self.task.kwargs['source']
        source_id = self.task.kwargs['source_id']
        target_url = self.task.kwargs['target_url']
        bucket_name = self.task.kwargs['bucket_name']
        file_prefix = self.task.kwargs['file_prefix']
        is_poi_task = self.task.kwargs.get('is_poi_task', True)
        need_insert_db = self.task.kwargs.get('need_insert_db', True)
        special_file_name = self.task.kwargs.get('special_file_name', '')

        # /album/user/2225/43/Q0tXRx4EY00/index/980x576
        if target_url.startswith('http://pic.qyer.com'):
            if target_url.endswith('/index'):
                target_url += '/980x576'
            if target_url.endswith('/index/'):
                target_url += '980x576'

        flag = None
        h = None
        w = None

        file_name = ''

        with MySession(need_cache=True) as session:
            @func_time_logger
            def img_file_get():
                _page = session.get(target_url, timeout=(3600, 3600))
                return _page

            page = img_file_get()

            f_stream = StringIO(page.content)

            if f_stream.len > 10485760:
                # 大于 10MB 的图片信息不入库
                raise ServiceStandardError(error_code=ServiceStandardError.IMG_TOO_LARGE)

            file_md5 = get_stream_md5(f_stream)
            flag, h, w = is_complete_scale_ok(f_stream)

            try:
                suffix = target_url.rsplit('.', 1)[1]
                # 对于 qyer 的图片特殊处理，无文件后缀
                if len(suffix) > 16:
                    suffix = ''
            except IndexError as e:
                suffix = page.headers['Content-Type'].split('/')[1]

            # 无文件后缀名图片直接 md5
            if suffix:
                file_name = hashlib.md5(target_url).hexdigest() + '.' + suffix
            else:
                file_name = hashlib.md5(target_url).hexdigest()

            if flag in [1, 2]:
                raise ServiceStandardError(error_code=ServiceStandardError.IMG_INCOMPLETE)
            else:
                # get img p hash
                _p_hash = img_p_hash(StringIO(page.content))

                # save file stream
                r2 = True
                if bucket_name != 'mioji-wanle':
                    r1 = upload_ks_file_stream(bucket_name, file_name, StringIO(page.content),
                                               page.headers['Content-Type'], hash_check=file_md5)
                else:
                    r1 = upload_ks_file_stream(bucket_name, '{}/'.format(file_prefix) + file_name,
                                               StringIO(page.content),
                                               page.headers['Content-Type'], hash_check=file_md5)
                if bucket_name == 'mioji-attr':
                    r2 = upload_ks_file_stream('mioji-shop', file_name, StringIO(page.content),
                                               page.headers['Content-Type'], hash_check=file_md5)

                if not (r1 and r2):
                    raise ServiceStandardError(ServiceStandardError.IMG_UPLOAD_ERROR)

            use_flag = 1 if flag == 0 else 0
            size = str((h, w))

            # 更新 file name
            if special_file_name != '':
                file_name = special_file_name

            # bucket_name = file_path.split('_')[1] + '_bucket' if is_poi_task else ''

            data = (
                source,  # source
                source_id,  # source_id
                target_url,  # pic_url
                file_name,  # pic_md5
                self.task.task_name[-9:],  # part
                size,  # size
                use_flag,  # poi use , hotel flag
                file_md5,  # file_md5
                bucket_name,  # poi rest attr shop
                json.dumps({"p_hash": _p_hash}),  # img phash for check duplicate
            )

            try:
                table_name = self.task.task_name
                if need_insert_db:
                    if is_poi_task:
                        poi_make_kw(data, table_name)
                    else:
                        hotel_make_kw(data, table_name)

                # 设置标识位
                self.task.error_code = 0
            except exc.SQLAlchemyError as err:
                raise ServiceStandardError(ServiceStandardError.MYSQL_ERROR, wrapped_exception=err)
            except IOError as err:
                raise ServiceStandardError(ServiceStandardError.IMG_UPLOAD_ERROR, wrapped_exception=err)

        # 被过滤的图片返回错误码不为 0
        if flag in [3, 4, 5]:
            raise ServiceStandardError(ServiceStandardError.IMG_SIZE_FILTER)
        self.task.error_code = 0
        return flag, h, w, self.task.error_code, bucket_name, file_name, self.task.task_name
