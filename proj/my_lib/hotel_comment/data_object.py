import hashlib
import pymysql

SQL_DICT = {
    'host': '10.10.180.145',
    'user': 'hourong',
    'passwd': 'hourong',
    'charset': 'utf8',
    'db': 'hotel_comment'
}


def _get_md5(source):
    return hashlib.md5(source).hexdigest()


class Review(object):
    def __init__(self, source):
        self.source = source
        self._sid = ''
        self._cid = ''
        self._username = ''
        self._language = ''
        self._rating = -1
        self._date = ''
        self._title = ''
        self._comment = ''

        self._flag = False

        self.sql = 'insert ignore into comment(source,sid,cid,date,username,language,rating,title,comment,comment_key) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        self._raw_sql = 'insert ignore into comment(source,sid,cid,date,username,language,rating,title,comment,comment_key) values("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")'

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        if value is not None:
            self._comment = value

    @property
    def sid(self):
        return self._sid

    @sid.setter
    def sid(self, value):
        if value is not None:
            self._sid = value

    @property
    def cid(self):
        return self._cid

    @cid.setter
    def cid(self, value):
        if value is not None:
            self._cid = value

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        if value is not None:
            self._date = value

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if value is not None:
            self._username = value

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value):
        if value is not None:
            self._language = value

    @property
    def rating(self):
        return self._rating

    @rating.setter
    def rating(self, value):
        if value is not None:
            self._rating = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if value is not None:
            self._title = value

    @property
    def flag(self):
        return self._flag

    def get_sql(self):
        return self.sql

    def get_raw_sql(self):
        return self._raw_sql % self.get_args()

    def get_args(self):
        return (self.source, self.sid, self.cid, self.date, self.username, self.language, self.rating, self.title,
                self.comment, _get_md5(self.comment))

    def save(self):
        if self.sid and self.comment:
            self._flag = True
            conn = pymysql.connect(**SQL_DICT)
            with conn as cursor:
                res = cursor.execute(query=self.get_sql(), args=self.get_args())
            conn.close()
            return res
        else:
            return 0

    def __str__(self):
        return '\t'.join(map(lambda x: str(x), self.get_args()))

    def __repr__(self):
        return '\t'.join(map(lambda x: str(x), self.get_args()))


if __name__ == '__main__':
    br = Review('booking')
    br.comment = None
    br.date = None
    br.rating = None
    print br
    print br.save()
