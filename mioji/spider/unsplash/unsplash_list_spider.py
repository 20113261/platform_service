# -*- coding: utf-8 -*-
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import json
from mioji.common.spider import Spider, request, PROXY_NONE
import re
from mioji.common import parser_except


class UnSplishSpider(Spider):
    source_type = 'unsplash|image_list'
    targets = {'image': {}}
    old_spider_tag = {'unsplash|image_list': {'required': ['image']}}

    def targets_request(self):
        content = json.loads(self.task.content)
        query = content.get('key', '')
        page = content.get('page', '')
        page = page + 1

        params = dict(query=query, page=page, per_page=20, collections='', orientation='')

        headers = {
            'authorization': 'Client-ID c94869b36aa272dd62dfaeefed769d4115fb3189a9d1ec88ed457207747be626'
        }

        @request(retry_count=4, proxy_type=PROXY_NONE, binding=self.parse_image)
        def get_pic_list():
            return {
                'req': {
                    'method': 'get',
                    'url': 'https://api.unsplash.com/search/photos',
                    'headers': headers,
                    'params': params,
                },
            }
        yield get_pic_list

    def response_error(self,req, resp, error):
        if resp.status_code == 500 and u'500 Server Error: Internal Server Error for url' in error.message:
            raise parser_except.ParserException(29, '页码过大')

    def parse_image(self, req, resp):
        data = json.loads(resp)
        all_pics = data.get('results')
        # [{}]
        r_t = []
        if not all_pics:
            return []
        for pic in all_pics:
            types = re.compile(r'fm=(\w+)').findall(pic['urls']['thumb'])[0]
            r_t.append({'id': pic['id'], 'thumbnail': pic['urls']['thumb'], 'preview': pic['urls']['regular'],
                        'suffix': types, "width": pic['width'], "height": pic["height"]})
        return r_t


if __name__ == "__main__":
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new
    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new

    task = Task()
    task.content = json.dumps({"key": "cat", "page": 3})
    spider = UnSplishSpider()
    spider.task = task
    code = spider.crawl()
    print code
    print json.dumps(spider.result, ensure_ascii=False)
    print len(spider.result['image'])
