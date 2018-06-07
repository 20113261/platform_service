#coding:utf-8
# @Time    : 2018/5/28
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : _test_mq.py
# @Software: PyCharm

import urllib,urllib2
import json
import base64
import pyrabbit
from proj.celery import app
# 类
class MQManage(object):
    def __init__(self):
        self._conn = None
        self._host = 'http://47.93.188.221:12345'
        self._username = None
        self._password = None
        self._vhost = 'serviceplatform'
#创建一个连接
    def create_connection(self,host,username,password):
        try:
            self._username = username
            self._password = password
            url = "http://"+host + ":15672/api/whoami"
            self._host = "http://"+host
            userInfo = "%s:%s" % (username, password)
            userInfo = base64.b64encode(userInfo.encode('UTF-8'))
            auth = 'Basic ' + userInfo#必须的
            request = urllib2.Request(url)
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', auth)
            response = urllib2.urlopen(request)
            self._conn = auth
        except Exception, e:
            return None
#设置用户权限
    def set_user_vhost(self, vhost='/', configure='.*', write='.*', read='.*'):
        try:
            url = self._host + ':15672/api/permissions/%2F/'
            url += self._username
            body = {}
            body['username'] = self._username
            body['vhost'] = vhost
            body['configure'] = configure
            body['write'] = write
            body['read'] = read
            data = json.dumps(body)
            request = urllib2.Request(url, data)
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', self._conn)
            request.get_method = lambda: "PUT"
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            response = urllib2.urlopen(request)
            res = response.read()
            return res
        except Exception, e:
            # print str(e)
            return None
#列出所有用户
    def list_users(self):
        try:
            url = self._host + ":15672/api/users"
            request = urllib2.Request(url)
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', self._conn)
            response = urllib2.urlopen(request)
            return response.read()
        except Exception, e:
            return None
#列出所有队列
    def list_queues(self):
        try:
            url = self._host + ":15672/api/queues"
            request = urllib2.Request(url)
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', self._conn)
            response = urllib2.urlopen(request)
            return response.read()
        except Exception, e:
            return None
#列出所有交换机
    def list_exchanges(self):
        try:
            url = self._host + ":15672/api/exchanges"
            request = urllib2.Request(url)
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', self._conn)
            response = urllib2.urlopen(request)
            exchanges = response.read()
            return exchanges
        except Exception, e:
            return None
#列出所有连接
    def list_connections(self):
        try:
            url = self._host + ":15672/api/connections"
            request = urllib2.Request(url)
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', self._conn)
            response = urllib2.urlopen(request)
            exchanges = response.read()
            return exchanges
        except Exception, e:
            return None
#显示每个连接的详细信息
    def show_connection_detail(self,connection):

        #10.0.0.245%3A44104%20-%3E%2010.0.0.158%3A5672%20(1)
        try:
            con = urllib.quote_plus( connection,safe='(,),' )
            url = self._host + ':15672/api/channels/'+ con
            url = url.replace('+','%20')
            # url = 'http://10.0.0.158:15672/api/connections/10.0.0.245%3A30078%20-%3E%2010.0.0.158%3A5672/channels'
            request = urllib2.Request( url )
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', self._conn)
            response = urllib2.urlopen(request)
            detail = response.read()
            return detail
        except Exception, e:
            print str(e)
            return None

    def clear_exchanges(self):
        exchanges = self.list_exchanges()
        for exchange in exchanges:
            self.del_exchange(exchange_name=exchange['name'])

    def clear_queues(self):
        queues = self.list_queues()
        for queue in queues:
            self.del_queue(queue_name=queue['name'])

    def del_exchange(self, exchange_name):
        try:
            url = self._host + ':15672/api/exchanges/%2F/'
            url += exchange_name
            body = {}
            body['vhost'] = self._vhost
            body['name'] = exchange_name
            data = json.dumps(body)
            request = urllib2.Request(url, data)
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', self._conn)
            request.get_method = lambda: "PUT"
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            response = urllib2.urlopen(request)
            res = response.read()
            return res
        except Exception, e:
            return None

    def del_queue(self, queue_name ):
        try:
            url = self._host + '/api/queues/%2F/'
            url += queue_name
            body = {}
            body['vhost'] = self._vhost
            body['name'] = queue_name
            data = json.dumps(body)
            request = urllib2.Request(url, data)
            request.add_header('content-type', 'application/json')

            username = 'zxp'
            password = 'zxp'  # 你信这是密码吗？

            base64string = base64.encodestring(
                '%s:%s' % (username, password))[:-1]  # 注意哦，这里最后会自动添加一个\n
            authheader = "Basic %s" % base64string
            request.add_header("Authorization", authheader)

            # request.add_header('authorization', self._conn)
            request.get_method = lambda: "DELETE"
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            response = urllib2.urlopen(request)
            res = response.read()
            return res
        except Exception, e:
            return None

    def add_vhost(self, vhost_name):
        try:
            url = self._host + ":15672/api/vhosts/"
            url = url + vhost_name
            body = {}
            body['name'] = vhost_name
            data = json.dumps(body)
            request = urllib2.Request(url, data)
            request.add_header('content-type', 'application/json')
            request.add_header('authorization', self._conn)
            request.get_method = lambda: "PUT"
            urllib2.build_opener(urllib2.HTTPHandler)
            response = urllib2.urlopen(request)
            res = response.read()
            return None
        except Exception, e:
            print str(e)
            return None

if __name__ == '__main__':
    import datetime
    now = datetime.datetime.now() + datetime.timedelta(seconds=20)
    expire = datetime.datetime.now() + datetime.timedelta(seconds=30)
    print(now)
    # app.send_task('proj.total_tasks.test_zxp', queue='zxp1', kwargs={'task': '优先级8'}, property=8)
    for i in range(5000):
        app.send_task('proj.total_tasks.test_zxp', queue='hotel_list_hiltion', kwargs={'task': i}, countdown=5)
    # app.send_task('proj.total_tasks.test_zxp', queue='zxp1', kwargs={'task': '优先级9'}, property=9)
    # app.send_task('proj.total_tasks.test_zxp', queue='zxp1', kwargs={'task': '优先级6'}, property=6)
    # app.send_task('proj.total_tasks.test_zxp', queue='zxp1', kwargs={'task': '优先级7'}, property=7)
    # for i in range(20, 50):
    #     app.send_task('proj.total_tasks.test_zxp', queue='zxp1', kwargs={'task': i}, eta=now)



    a = pyrabbit.Client('47.93.188.221:12345', 'zxp', 'zxp')
    print()
    # # a = pyrabbit.Client('10.10.189.213:5672', 'hourong', '1220')
    #
    # m = MQManage()
    # m.del_queue('zxpzxp')