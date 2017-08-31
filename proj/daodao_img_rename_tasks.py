# coding=utf-8
import pymysql
import os
import hashlib
import redis
import shutil
import traceback
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.is_complete_scale_ok import is_complete_scale_ok
from proj.my_lib.task_module.task_func import update_task


def get_md5(src):
    return hashlib.md5(src.encode()).hexdigest()


def file_md5(f_name):
    hash_md5 = hashlib.md5()
    with open(f_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def insert_db(args, table_name):
    conn = pymysql.connect(host='10.10.189.213', user='yanlihua', passwd='yanlihua', charset='utf8', db='update_img')
    with conn as cursor:
        res = cursor.execute(
            'insert into {0} (file_name,sid,url,bucket_name,pic_size,url_md5,pic_md5,source,`use`,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(
                table_name),
            args)
    conn.close()
    return res

def insert_db_new(args, table_name):
    conn = pymysql.connect(host='10.10.189.213', user='yanlihua', passwd='yanlihua', charset='utf8', db='update_img')
    with conn as cursor:
        res = cursor.execute(
            'insert into {0} (file_name, source, sid, url, pic_size, bucket_name, url_md5, pic_md5, `use`, part) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(
                table_name),
            args)
    conn.close()
    return res


@app.task(bind=True, base=BaseTask, max_retries=1)
def daodao_img_rename_task(self, file_name, src_path, dst_path, bucket_name, img_url, mid, table_name, **kwargs):
    self.task_source = 'TripAdvisor'
    self.task_type = 'ImgRename'

    try:
        src_file = os.path.join(src_path, file_name)
        flag, h, w = is_complete_scale_ok(src_file)
        f_md5 = file_md5(src_file)
        size = unicode((h, w))
        if flag == 0 or flag == 4:
            __used = u'1' if flag == 0 else u'0'
            data = (file_name, unicode(mid), unicode(img_url), unicode(bucket_name), size,
                    unicode(file_name).replace(u'.jpg', u''),
                    unicode(f_md5),
                    u'machine', __used, u'online')
            try:
                # 暂时没有解决这三个函数的事务关系，所以将重要性最低的函数前置执行
                shutil.copy(src_file, os.path.join(dst_path, file_name))
                print insert_db(data, table_name)
            except Exception as e:
                raise e
            update_task(kwargs['task_id'])
        else:
            raise Exception('Error Flag')
    except Exception as exc:
        self.retry(exc=traceback.format_exc(exc))

@app.task(bind=True, base=BaseTask, max_retries=8)
def daodao_img_filter_task(self, file_name, src_path, dst_path, bucket_name, img_url, source, source_id, part, **kwargs):
    self.task_source = 'TripAdvisor_new'
    self.task_type = 'ImgRename_new'

    src_file = os.path.join(src_path, file_name)
    flag, h, w = is_complete_scale_ok(src_file)
    f_md5 = file_md5(src_file)
    size = unicode((h, w))
    if not (flag == 0 or flag == 4):
        raise Exception('Error Flag')

    url_md5 = hashlib.md5(img_url).hexdigest()
    __used = u'1' if flag == 0 else u'0'
    data = (file_name, source, source_id, img_url, size, bucket_name, url_md5, f_md5, __used, part)
    try:
        # 暂时没有解决这三个函数的事务关系，所以将重要性最低的函数前置执行
        shutil.copy(src_file, os.path.join(dst_path, file_name))
        print insert_db_new(data, 'poi_bucket_relation')
    except Exception as e:
        raise e

