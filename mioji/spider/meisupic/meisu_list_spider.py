# coding=utf-8
from mioji.common.utils import setdefaultencoding_utf8
from mioji.common.spider import Spider, request, PROXY_NONE
from mioji.common.task_info import Task
import re
import json
import requests
from mioji.common.logger import logger

setdefaultencoding_utf8()


url = 'http://buy.meisupic.com/'
size_url = 'http://buy.meisupic.com/goods.php'


class MeiSuSpider(Spider):
    source_type = 'meisupic|image_list'

    targets = {
        'image': {
        }
    }
    old_spider_tag = {
        'meisupic|image_list': {'required': ['image']}
    }

    def targets_request(self):
        content = json.loads(self.task.content)
        keyword = content.get('key', '')
        page = content.get('page', '')

        page = page + 1

        data = {
               'keyword': keyword,
               'sort': 4,
               'page': page,
            }

        @request(retry_count=4, proxy_type=PROXY_NONE, binding=self.parse_image)
        def get_flight_data():
            return {
                'req': {
                    'method': 'post',
                    'url': url,
                    'data': data
                }
            }
        yield get_flight_data

    def parse_image(self, req, resp):
        html = re.compile(r'{.*}').findall(resp)[0]
        goods_list = json.loads(html)['goods_list']
        result, item = [], {}
        if not goods_list:
            return []
        for goods in goods_list:
            size_data = {
                'id': goods['id']
            }
            size_response = requests.post(size_url, data=size_data)

            size_dict = json.loads(re.compile(r'{.*}').findall(size_response.content)[0])

            size = sorted(size_dict.keys())[-1]

            types = re.compile(r'api_thumb_\d+\.(\w+)').findall(goods['goods_thumb_api'])[0]
            result.append({'id': goods['id'], 'thumbnail': goods['goods_thumb_api'],
                           'preview': goods['goods_thumb_api'], 'suffix': types,
                           "height": int(size_dict[size]['height']), "width": int(size_dict[size]['width'])})

        return result


if __name__ == '__main__':

    task = Task()
    task.content = json.dumps({'key': '儿童', 'page': 1222})
    mei_su = MeiSuSpider()
    mei_su.task = task
    code = mei_su.crawl()
    print code
    print mei_su.result
