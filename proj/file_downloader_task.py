#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/15 上午11:15
# @Author  : Hou Rong
# @Site    : 
# @File    : file_downloader_task.py
# @Software: PyCharm
import datetime
import os
import re

from StringIO import StringIO
from proj.my_lib.Common.MongoLog import save_log
from proj.my_lib.is_complete_scale_ok import is_complete_scale_ok
from .celery import app
from .my_lib.BaseTask import BaseTask
from my_lib.Common.Browser import MySession
from my_lib.Common.Utils import get_md5, get_local_ip
from pyPdf import PdfFileReader
from my_lib.Common.RedisAlreadyDownload import AlreadyDownload


# alreadyDownload = AlreadyDownload()


def get_content_length_and_type(url, session):
    headers = {
        'Range': 'bytes=0-4'
    }
    session.headers.update(headers)

    r = session.head(url)

    content_type = 'unknown'
    try:
        content_type = r.headers['content-type']
    except Exception:
        pass

    total = 0
    try:
        content_range = r.headers['content-range']
        total = int(re.match(ur'^bytes 0-4/(\d+)$', content_range).group(1))
        return total, content_type
    except Exception:
        pass
    try:
        total = int(r.headers['content-length'])
    except Exception:
        pass
    return total, content_type


def get_file_name(url, c_type):
    c_suffix = c_type.split(';')[0].split('/')[-1].strip()
    url_md5 = get_md5(url)
    return '{0}.{1}'.format(url_md5, c_suffix)


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='1/s')
def file_downloader(self, url, file_type, file_path, need_filter="YES", file_split="YES", **kwargs):
    """
    :param self:
    :param url: 需要下载文件的 url
    :param file_type: 文件类型 img、pdf 等等，img 会检查文件是否完整下载
    :param file_path:
    :param need_filter: is it need file size filter YES or NO
    :param file_split: 是否需要分块下载
    :param kwargs:
    :return:
    """
    self.task_source = 'Any'
    self.task_type = 'FileDownload'
    # print '+++++++++++++++++++++++++++++++++++\n', url, '\n+++++++++++++++++++++++++++++++++++'
    with MySession() as session:
        # 将去重放在 Task 中完成，本部分不做去重处理
        # # 已经下载的，不下载
        # if alreadyDownload.has_crawled(url):
        #     return None

        # 获取文件大小
        total_length, content_type = get_content_length_and_type(url, session)

        # 小于 20KB 不下载
        if total_length < 20480 and need_filter == "YES":
            # alreadyDownload.add_url(url, '|_||_|'.join(['filter', get_local_ip(), str(total_length)]))
            save_log(
                '|_||_|'.join(['filter', get_local_ip(), str(total_length)]),
                kwargs['mongo_task_id'],
                'attr_file_download'
            )
            return None
        file_path = '/Users/luwn/test/image'
        # 文件下载
        file_name = get_file_name(url, content_type)

        if not os.path.exists(file_path):
            os.makedirs(file_path)

        # 生成文件路径
        file_absolute_dir = os.path.join(file_path, file_name)

        # 流下载，先去除 header 中的 Range ，再下载
        session.headers.pop('Range')

        file_req = session.get(url, stream=True)
        if file_req.status_code != 200:
            session.file_req = file_req

        if file_split == "YES":
            # fixme 当一个任务被多次分发后，会出现同步问题，A 在写数据，B 会覆盖。使用全量下载更新不会出现该问题
            with open(file_absolute_dir, 'wb') as f:
                for chunk in file_req.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            with open(file_absolute_dir, 'rb') as downloaded_file:
                if file_type == 'img':
                    flag, h, w = is_complete_scale_ok(downloaded_file)
                    if flag in [1, 2]:
                        # 当文件不符合要求的时候删除
                        os.remove(file_absolute_dir)
                        raise Exception('The file (type {}) is not fully loaded'.format(file_type))
                elif file_type == 'pdf':
                    try:
                        doc = PdfFileReader(downloaded_file)
                    except Exception:
                        # 当文件不符合要求的时候删除
                        os.remove(file_absolute_dir)
                        raise Exception('The file (type {}) is not fully loaded'.format(file_type))
        else:
            file_bytes = b''
            for chunk in file_req.iter_content(chunk_size=1024):
                if chunk:
                    file_bytes += chunk

            memory_file_obj = StringIO(file_bytes)
            if file_type == 'img':
                flag, h, w = is_complete_scale_ok(memory_file_obj)
                if flag in [1, 2]:
                    raise Exception('The file (type {}) is not fully loaded'.format(file_type))
            elif file_type == 'pdf':
                try:
                    doc = PdfFileReader(memory_file_obj)
                except Exception:
                    raise Exception('The file (type {}) is not fully loaded'.format(file_type))

            with open(file_absolute_dir, 'wb') as f:
                f.write(file_bytes)

        # todo 完成任务通知
        # alreadyDownload.add_url(url, '|_||_|'.join(
        #     ['succeed', get_local_ip(), str(file_absolute_dir), str(total_length)]))
        save_log(
            '|_||_|'.join(['succeed', get_local_ip(), str(file_absolute_dir), str(total_length)]),
            kwargs['mongo_task_id'],
            'attr_file_download'
        )
        return file_absolute_dir


if __name__ == '__main__':
    file_downloader(file_downloader, 'https://ccm.ddcdn.com/ext/photo-s/0a/85/77/19/caption.jpg', 'img', '/Users/luwn/test', need_filter="NO", file_split="NO")