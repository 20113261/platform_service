import hashlib

import db_img

'''
| source      | varchar(20)  | NO   | PRI | NULL              |                             |
| source_id   | varchar(256) | NO   | PRI |                   |                             |
| pic_url     | text         | YES  |     | NULL              |                             |
| pic_md5     | varchar(512) | NO   |     | NULL              |                             |
| part        | varchar(10)  | YES  |     | NULL              |                             |
| hotel_id    | varchar(20)  | NO   |     | NULL              |                             |
| status      | varchar(10)  | NO   |     | -1                |                             |
| update_date | timestamp    | NO   |     | CURRENT_TIMESTAMP | on update CURRENT_TIMESTAMP |
| size        | varchar(40)  | YES  |     |                   |                             |
| flag        | varchar(10)  | YES  |     | 1                 |                             |
'''


def get_file_md5(f_name):
    hash_md5 = hashlib.md5()
    with open(f_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def insert_db(args):
    sql = 'insert into pic_relation_new (`source`,`source_id`,`pic_url`,`pic_md5`,`part`,`size`,`flag`, `file_md5`) VALUES (%s,%s,%s,%s,%s,%s,%s, %s)'
    return db_img.ExecuteSQL(sql, args)


def insert_too_large(args):
    sql = 'insert into TooLargePic (`file_name`,`file_size`) VALUES (%s,%s)'
    return db_img.ExecuteSQL(sql, args)


if __name__ == '__main__':
    print get_file_md5('/search/image/hotelinfo_zls_lx20161226_img/fff91daa07bc091d791e08bcfa8a9a28.jpg')
