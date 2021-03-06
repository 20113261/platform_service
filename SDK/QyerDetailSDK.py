# coding=utf-8

from sqlalchemy.sql import text

from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.Common.Browser import MySession
from proj.my_lib.Common.KeyMatch import key_is_legal
from proj.my_lib.Common.NetworkUtils import google_get_map_info
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.ServiceStandardError import TypeCheckError
from proj.my_lib.logger import get_logger
from proj.my_lib.my_qyer_parser.data_obj import DBSession
from proj.my_lib.my_qyer_parser.my_parser import page_parser
from proj.my_lib.new_hotel_parser.data_obj import text_2_sql
from proj.my_lib.Common.Utils import retry

logger = get_logger("QyerPoiDetail")


class QyerDetailSDK(BaseSDK):
    @retry(times=3)
    def _execute(self, **kwargs):
        with MySession(need_cache=True, need_proxies=True) as session:
            city_id = self.task.kwargs['city_id']
            target_url = self.task.kwargs['target_url']
            headers = {
                'Host': 'place.qyer.com'
            }
            page = session.get(
                target_url,
                headers=headers,
                timeout=240
            )
            page.encoding = 'utf8'
            content = page.text

            if '请输入验证码' in content:
                raise Exception("请输入验证码")

            result = page_parser(content=content, target_url=target_url)
            result.city_id = city_id
            name = result.name
            name_en = result.name_en
            map_info = result.map_info
            address = result.address

            map_info_is_legal = True
            try:
                lon, lat = map_info.split(',')
                if float(lon) == 0.0 and float(lat) == 0.0:
                    map_info_is_legal = False
            except Exception as e:
                map_info_is_legal = False
                logger.exception(msg="[map info is not legal]", exc_info=e)

            if not key_is_legal(map_info) or not map_info_is_legal:
                if not key_is_legal(address):
                    # todo 临时注释
                    pass
                    # raise TypeCheckError(
                    #     'Error map_info and address NULL        with parser %ss    url %s' % (
                    #         page_parser.func_name, target_url))
                google_map_info = google_get_map_info(address)
                if not key_is_legal(google_map_info):
                    # todo 临时注释
                    pass
                    # raise TypeCheckError(
                    #     'Error google_map_info  NULL  with [parser: {}][url: {}][address: {}][map_info: {}]'.format(
                    #         page_parser.func_name, target_url, address, map_info)
                    # )
                result.map_info = google_map_info

            if key_is_legal(name) or key_is_legal(name_en) or map_info_is_legal or key_is_legal(result.introduction):
                logger.info(name + '  ----------  ' + name_en)
            else:
                # raise TypeCheckError(
                #     'Error name and name_en Both NULL        with parser %s    url %s' % (
                #         page_parser.func_name, target_url))
                raise TypeCheckError("All Available Key is Null")

        sql_result = result.__dict__
        sql_key = sql_result.keys()
        if '_sa_instance_state' in sql_key:
            sql_key.remove('_sa_instance_state')

        try:
            session = DBSession()
            session.execute(text(text_2_sql(sql_key).format(table_name=self.task.task_name)), [sql_result])
            session.commit()
            session.close()
        except Exception as e:
            self.logger.exception(msg="[mysql exec err]", exc_info=e)
            raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        self.task.error_code = 0
        return self.task.error_code
