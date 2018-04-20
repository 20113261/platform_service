# -*- coding: utf-8 -*-
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ, w_get_proxy, slave_get_proxy
from mioji.common import parser_except
import requests
from io import BytesIO

from mioji.common.download_file import ks_upload_file_stream


class UnsplishDownloadSpider(Spider):
    source_type = 'unsplash|image_download'

    targets = {
        'image': {
        }
    }
    old_spider_tag = {
        'unsplash|image_download': {'required': ['image']}
    }

    def crawl(self, required=None, cache_config=None):
        pic_id = self.task.ticket_info.get('id', '')
        url = 'https://unsplash.com/photos/{}/download'.format(pic_id)
        retry = 4
        r = ''
        while not r and retry > 0:
            try:
                logger.info('开始下载' + url)
                r = requests.get(url, timeout=120).content
            except Exception as e:
                logger.error(str(e), exc_info=True)
                logger.info('下载失败，剩余重试次数' + str(retry))
                retry -= 1
        if retry == 0 and not r:
            logger.error('下载失败')
            raise parser_except.ParserException(12, 'fail to download')
        logger.info('下载成功, 长度是' + str(len(r)))

        self.file_obj = BytesIO(r)

        r = self.parse_image(None, {'url': ''})
        self.code = 0 if r else 12
        return self.code


    def targets_request(self):
        pass

    def parse_image(self, req, resp):
        bucket_name = self.task.ticket_info['bucket_name']
        upload_key = self.task.ticket_info['image_name']
        path = self.task.ticket_info['path']
        if path:
            upload_key = path + "/" + self.task.ticket_info['image_name']
        md5 = ks_upload_file_stream.get_stream_md5(self.file_obj)
        result = ks_upload_file_stream.upload_ks_file_stream(bucket_name, upload_key, self.file_obj, hash_check=md5)
        return [str(result)]


if __name__ == "__main__":
    from mioji.common.task_info import Task
    import mioji.common.spider

    task = Task()
    # task.ticket_info = {'img': {'bucket_name': 'mioji-wanle', 'upload_key':'huantaoyou/hello_world', 'id': '3CErUWqAzmg'}}
    task.ticket_info = {'id': 22, 'unionKey': '22', 'host': 'host', 'bucket_name': 'bucket_name', 'image_name': 'image_name', "path":'ee'}

    spider = UnsplishDownloadSpider()
    spider.task = task
    code = spider.crawl()
    print code
    print spider.result