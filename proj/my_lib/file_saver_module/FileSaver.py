import collections
import hashlib
import json
import zlib

import os
import pymysql
import six
from pymysql.err import IntegrityError

DataPath = '/data/FileSaver'


def get_md5(src):
    return hashlib.md5(src).hexdigest()


class FileSaverBase(object):
    __DataPath__ = None
    __SQLDict__ = None

    def __init__(self):
        if self.__DataPath__ is None:
            raise Exception('Abstract Class Need To Init')
        self.path = self.__DataPath__
        self.conn = pymysql.connect(**self.__SQLDict__)
        self.cursor = self.conn.cursor()

    def save(self, task_id, args, content):
        _out = zlib.compress(content.encode())
        _file_md5 = get_md5(_out)
        _file_dir = os.path.join(self.path, _file_md5)
        if not os.path.exists(_file_dir):
            _f = open(_file_dir, 'wb')
            _f.write(_out)
        _id = get_md5((task_id + _file_md5).encode())
        data = (_id, json.dumps(args), task_id, _file_md5)
        try:
            self._save_key(data)
        except IntegrityError as e:
            if 'Duplicate entry' not in e.args[1]:
                raise e
        return _id

    def _save_key(self, args):
        return self.cursor.execute('insert into FileSaver (`id`,`args`,`task_id`,`file_md5`) VALUES (%s,%s,%s,%s)',
                                   args=args)

    def load_file_list(self, task_id):
        return self._load_file_list(task_id=task_id)

    def _load_file_list(self, task_id, iter_forbid_type=(str, bytes,)):
        if isinstance(task_id, six.string_types):
            self.cursor.execute('SELECT id,file_md5 FROM FileSaver WHERE task_id=%s', (task_id,))
            for line in self.cursor.fetchall():
                yield line
        elif isinstance(task_id, collections.Iterable) and not isinstance(task_id, iter_forbid_type):
            if isinstance(task_id[0], six.string_types):
                self.cursor.execute('SELECT id,file_md5 FROM FileSaver WHERE task_id in ({})'.format(
                    ','.join(map(lambda x: '"' + x + '"', task_id))))
                for line in self.cursor.fetchall():
                    yield line
        else:
            raise TypeError('Unknown task_id type: ' + str(type(task_id)))

    def load_file(self, task_id):
        for _, file_md5 in self._load_file_list(task_id=task_id):
            yield self._load_file(file_md5=file_md5)

    def _load_file(self, file_md5):
        _file_path = os.path.join(self.path, file_md5)
        _f = open(_file_path, 'rb')
        return zlib.decompress(_f.read()).decode()

    def __del__(self):
        self.conn.close()


class FileSaver(FileSaverBase):
    __DataPath__ = '/data/FileSaver'
    __SQLDict__ = {'host': 'localhost', 'user': 'hourong', 'passwd': 'hourong', 'db': 'FileSaver', 'charset': 'utf8'}


if __name__ == '__main__':
    import requests

    page = requests.get('https://www.baidu.com/')
    page.encoding = 'utf8'
    content = page.text

    fs = FileSaver()
    # res = fs.save('dddd', {'asdf': 'asdf', 'fds': 123123}, content=content)
    # print(res)
    # for i in fs.load_file_list(('asdfasdfasdf', 'asfds', 'dddd')):
    #     print(i)
    for f in fs.load_file('asdfasdfsafd'):
        print(f)
