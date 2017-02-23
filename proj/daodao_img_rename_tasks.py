import pymysql
import os
import hashlib
import redis
import shutil
from .celery import app
from .my_lib.BaseTask import BaseTask
from .my_lib.is_complete_scale_ok import is_complete_scale_ok
from .my_lib.task_module.task_func import update_task

redis_dict = redis.Redis(host='10.10.180.145', port=6379, db=10)


def get_md5(src):
    return hashlib.md5(src.encode()).hexdigest()


def file_md5(f_name):
    hash_md5 = hashlib.md5()
    with open(f_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def insert_db(args):
    conn = pymysql.connect(host='10.10.189.213', user='yanlihua', passwd='yanlihua', charset='utf8', db='update_img')
    with conn as cursor:
        res = cursor.execute(
            'insert into {0} (file_name,sid,url,bucket_name,pic_size,url_md5,pic_md5,source,`use`,status) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            args)
    conn.close()
    return res


@app.task(bind=True, base=BaseTask, max_retries=3)
def daodao_img_rename_task(self, file_name, src_path, dst_path, bucket_name, img_url, mid, **kwargs):
    try:
        src_file = os.path.join(src_path, file_name)
        flag, h, w = is_complete_scale_ok(src_file)
        f_md5 = file_md5(src_file)
        size = unicode((h, w))
        if flag == 0:
            try:
                img_count = str(int(redis_dict.get(mid)) + 1)
            except Exception as e:
                raise e
            img_count += 1
            new_name = u'{0}_{1}.jpg'.format(mid, img_count)
            # (file_name, miaoji_id, url, BUCKET_NAME, size, md5_name, pic_md5, 'machine', '1','online')
            data = (new_name, unicode(mid), unicode(img_url), unicode(bucket_name), size,
                    unicode(file_name).replace(u'.jpg', u''),
                    unicode(f_md5),
                    u'machine', u'1', u'online')
            shutil.copy(src_file, os.path.join(dst_path, new_name))
            print insert_db(data)
            redis_dict.set(mid, img_count)
            update_task(kwargs['task_id'])
    except Exception as exc:
        self.retry(exc=exc)
