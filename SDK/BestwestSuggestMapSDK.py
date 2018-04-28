# coding=utf-8
import time
import pymongo
import requests
import pymongo.errors
from copy import deepcopy
import re

from mioji.spider_factory import factory
from proj.my_lib.Common.Task import Task
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.list_config import cache_config, none_cache_config
from proj.my_lib.logger import get_logger
from proj.my_lib.new_hotel_parser.hotel_parser import parse_hotel
from proj.mysql_pool import service_platform_pool
from mongo_pool import mongo_data_client
from proj.my_lib.models.HotelModel import CommonHotel
# from SupplementTask import google_get_map_info
from proj.my_lib.Common.NetworkUtils import google_get_map_info_zxp,map_info_get_google
from MongoTaskInsert import TaskType
from proj.my_lib.Common.KeyMatch import key_is_legal



# logger = get_logger("HotelDetailSDK")
client = pymongo.MongoClient(host='10.10.213.148')



class BestwestSuggestMapSDK(BaseSDK):
    def _execute(self, **kwargs):
        address = self.task.kwargs['description']
        self.logger.debug('-'*20)
        map_info = google_get_map_info_zxp(address)
        self.logger.debug('{0} --- {1}'.format(address, map_info))
        data_collections = client['CitySuggest'][self.task.task_name]
        # data_collections.create_index([('description', 1)], unique=True, background=True)
        content = deepcopy(self.task.kwargs)
        content['map_info'] = map_info
        self.logger.debug(map_info)
        map_info_is_legal = True
        try:
            lon, lat = map_info.split(',')
            if float(lon) == 0.0 and float(lat) == 0.0:
                map_info_is_legal = False
        except Exception as e:
            map_info_is_legal = False
            self.logger.exception(msg="[map info is not legal]", exc_info=e)
        self.logger.debug('*'*20)
        if key_is_legal(map_info) and map_info_is_legal:
            data_collections.insert(content)
            self.task.error_code = 0
        else:
            self.task.error_code = 12


if __name__ == '__main__':
    task = Task(_worker='', _queue='hotel_detail', _routine_key='hotel_detail', _task_id='demo', _source='hilton',
                _type='hotel',
                _task_name='list_hotel_bestwest_20180423a',
                _used_times=0, max_retry_times=3,
                kwargs={
                    # "url": "http://www.booking.com\n/hotel/ph/tg-hometel.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=3b827f3aa2e3fca0a95ec0d56605f64a;checkin=2018-01-08;checkout=2018-01-11;ucfs=1;soh=1;srpvid=511e686ec99000f9;srepoch=1511448670;highlighted_blocks=;all_sr_blocks=;room1=A%2CA;soldout=0%2C0;hpos=10;hapos=520;dest_type=region;dest_id=5374;srfid=0a39626563bec2b30fbbedccb1438d4e5f55493fX520;from=searchresults;soldout_clicked=1\n;highlight_room=#no_availability_msg",
                    # "url": "https://www.ihg.com/holidayinnexpress/hotels/cn/zh/teluk/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/TELUK/details",
                    # "url": "https://www.expedia.com.hk/Bhimtal-Hotels-Emerald-Trail.h4474316.Hotel-Information?chkin=2017%2F12%2F6&chkout=2017%2F12%2F7&rm1=a2&regionId=6139790&sort=recommended&hwrqCacheKey=b07edfbf-68f1-472b-b58d-d153dc82d7feHWRQ1511794413272&vip=false&c=c8d5ec02-71e2-496b-aa9f-5988e64b7931&",
                    # "url": "https://www.booking.com/hotel/us/new-lakefront-home-4br-47-2b-in-katy-west-houston.zh-cn.html?aid=376390;label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-11455299683%3Alp9061505%3Ali%3Adec%3Adm;sid=760b4b8ac503b49f5d89e67ec36a2fa9;aer=1;dest_id=20126498;dest_type=city;dist=0;hapos=90;hpos=15;room1=A%2CA;sb_price_type=total;spdest=ci%2F20126498;spdist=41.0;srepoch=1511794977;srfid=75643f0d9b7ac3fe31b60ecc58ba9f10b377fd16X90;srpvid=fdcc69d0f9a606d5;type=total;ucfs=1&#hotelTmpl",
                    # "url": "https://www.expedia.com.hk/Hotels-Beautiful.h19200665.Hotel-Information",
                    "place_id" : "ChIJXTYsUnqhTEcRVJwEAzzo-zE",
                    "part" : "20180423a",
                    "count" : 2,
                    "source": 'bestwest',
                    "id" : "d93f57e3684e251964e93d47eca295e92eb14c37",
                    "description": "英国霍利查尔伍德"
                },
                task_type='test', list_task_token=None)
    from proj.total_tasks import bestwest_suggest_map_task
    bestwest_suggest_map_task(task=task)
