# coding=utf-8
import json
from mioji.common.utils import setdefaultencoding_utf8
from mioji.common.spider import Spider
from mioji.common.logger import logger
from mioji.common.task_info import Task
import requests
import re
from mioji.common.download_file.ks_upload_file_stream import upload_ks_file_stream, get_stream_md5
from io import BytesIO

setdefaultencoding_utf8()


size_url = 'http://buy.meisupic.com/goods.php'
login_url = 'http://buy.meisupic.com/login.php'
download_url = 'http://buy.meisupic.com/down.php'


class MeiSuDownloadImgSpider(Spider):
    source_type = 'meisupic|image_download'

    targets = {
        'image': {
        }
    }
    old_spider_tag = {
        'meisupic|image_download': {'required': ['image']}
    }

    def targets_request(self):
        pass

    def crawl(self, required=None, cache_config=None):
        img_id = self.task.ticket_info['id']

        login_data = {
            'user_name': 'mioji',
            'secret_key': 'ASDJFSAJDF76541njsha'
        }
        login_after = requests.post(login_url, data=login_data)
        session_id = json.loads(login_after.content)['session_id']

        size_data = {
            'id': img_id
        }
        size_response = requests.post(size_url, data=size_data)

        size_dict = json.loads(re.compile(r'{.*}').findall(size_response.content)[0])
        size = sorted(size_dict.keys())[-1]
        download_data = {
            'session_id': session_id,
            'goods_sn': img_id,
            'goods_size': size,
        }
        logger.info('下载开始。。。')
        download = requests.post(download_url, data=download_data)
        logger.info('下载结束，图片大小为:{}'.format(len(download.content)))
        r = self.parse_image(download.content, '')

        self.code = 0 if r else 12
        return self.code

    def parse_image(self, req, resp):
        bucket_name = self.task.ticket_info['bucket_name']
        upload_key = self.task.ticket_info['image_name']
        path = self.task.ticket_info['path']
        if path:
            upload_key = path + "/" + self.task.ticket_info['image_name']
        f = BytesIO(req)
        md5 = get_stream_md5(f)

        result = upload_ks_file_stream(bucket_name, upload_key, f, hash_check=md5)
        return result


if __name__ == '__main__':
    task = Task()
    # task.ticket_info = {'img': {'bucket_name': 'mioji-wanle', 'upload_key':'huantaoyou/hello_world', 'id': 75657759}}

    task.ticket_info = {'id': 75657759, 'unionKey': '', 'host': '', 'bucket_name': "aab", 'image_name': 'aa', "path": ''}

    mei_su_download = MeiSuDownloadImgSpider()
    mei_su_download.task = task
    mei_su_download.crawl()



