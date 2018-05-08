# -*- coding: utf-8 -*-
from mioji.common import parser_except
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_NONE

from tongchengBase import flight_type

import json
import time
import hashlib
import base64
import gzip
from cStringIO import StringIO


class FlightApi(Spider):
    def __init__(self, task):
        Spider.__init__(self, task)

    def init(self):
        try:
            self.redis_key = getattr(self.task, 'redis_key', '')
            self.f_type = self.redis_key.split('|', 1)[0]
            auth = json.loads(self.task.ticket_info['auth'])
            self.url = auth['url']
            self.safe_code = auth['safe_code']
            self.pid = auth['pid']
            self.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            self.public_params = {
                'serviceCode': 'Search',
                'pid': self.pid,
                'sign': None,
                'requestID': str(time.time()),
                'timestamp': self.timestamp,
                'businessType': '1',
                'params': {}
            }
            self.sub_params = {
                'productType': '25',
                'childNumber': 0,
                'tripType': flight_type[self.f_type],
                'adultNumber': self.task.ticket_info['v_count'],
            }
        except Exception as e:
            logger.error(e)
            raise parser_except.ParserException(121, "检查一下auth信息")
        self.headers = {
            'Content-Type': 'text/plain'
        }

    def __sign(self, params):
        """
        签名方法 [参数 时间戳 安全码 pid]
        :param params:
        :return:
        """
        parameters = '%s%s%s%s' % (params, self.timestamp, self.safe_code, self.pid)
        sign = hashlib.md5(parameters).hexdigest()
        logger.info('签名 %s' % sign)
        return sign

    def __encryption(self, original_data):
        """
        先 GZIP 压缩 再 base64 编码
        :param original_data:
        :return:
        """
        buf = StringIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as g_file:
            g_file.write(original_data)
        encrypt = base64.b64encode(buf.getvalue())
        logger.info('编码后数据 %s' % encrypt)
        return encrypt

    def __decryption(self, encrypt_data):
        """
        先 base64 解码 再 GZIP 解压
        :param encrypt_data:
        :return:
        """
        buf = StringIO(base64.b64decode(encrypt_data))
        with gzip.GzipFile(fileobj=buf) as g_file:
            dict_resp = json.loads(g_file.read())
        logger.info('解码后数据 %s' % json.dumps(dict_resp, ensure_ascii=False))
        return dict_resp

    def targets_request(self):
        self.init()
        contents = self.task.content.split("|")
        for c in contents:
            content = c.split('&')
            self.sub_params['fromCity'], self.sub_params['toCity'], self.sub_params['fromDate'] = content[:3]
            if flight_type[self.f_type] == '2':
                self.sub_params['retDate'] = content[3]

        json_params = json.dumps(self.sub_params)
        self.public_params['sign'] = self.__sign(json_params)
        self.public_params['params'] = self.__encryption(json_params)
        logger.info(self.public_params)

        @request(retry_count=0, proxy_type=PROXY_NONE, binding=['Flight'])
        def get_response():
            return {
                'req': {
                    'method': 'POST',
                    'url': self.url,
                    'headers': self.headers,
                    'json': self.public_params
                },
                'data': {'content_type': 'xml'},
            }
        return [get_response,]

    def parse_Flight(self, req, resp):
        decrypt_resp = self.__decryption(resp)
        if decrypt_resp['code']!='LY000000':
            raise parser_except.ParserException(89, decrypt_resp['msg'])
        if decrypt_resp.get('routings', None):
            return self.parse_detail(req, decrypt_resp)
        else:
            return []

    def parse_detail(self, req, resp):
        """继承此方法"""


if __name__ == '__main__':
    from mioji.common.task_info import Task
    task = Task()
    task.redis_key = 'flight|10001|20001|20180129|20180130|CA934'
    task.content = "PEK&ICN&20180322&20180323"
    task.other_info = {}
    task.ticket_info = {"v_count": 1,
                        'v_seat_type': 'E',
                        "auth": json.dumps({
                            # "url": "http://tcflightopenapi.t.17usoft.com/flightdistributeapi/dispatcher/api",#测试补鞥用
                            "url": "http://tcflightopenapi.17usoft.com/flightdistributeapi/dispatcher/api",#正式能用
                            "safe_code": "5fe87fe834c2e726",
                            "pid": "6a054f5fda424be5947ff1124c1f66af",
                            "session_key": "6101b16a2bb5ea1b3844ed78120ffe8b919e840dbd0f9c72074082786"
                        })}
    spider = FlightApi(task)

    spider.task = task
    result_code = spider.crawl()
    print result_code
    print spider.result['Flight']