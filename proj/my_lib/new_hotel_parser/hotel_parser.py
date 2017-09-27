# coding=utf-8
import agoda_parser
import booking_parser
import ctrip_cn_parser
import ctrip_parser
import elong_parser
import expedia_parser
import hilton_parser
import hotels_parser
import hoteltravel_parser
import hrs_parser
import tripadvisor_parser
from proj.my_lib.Common.KeyMatch import key_is_legal
from proj.my_lib.Common.Utils import google_get_map_info
from proj.my_lib.StandError import TypeCheckError
from proj.my_lib.logger import get_logger
from .lang_convert import tradition2simple

logger = get_logger("HotelDetail")


def parse_hotel(content, url, other_info, source, part, retry_count):
    function_dict = {
        'agoda': agoda_parser.agoda_parser,
        'booking': booking_parser.booking_parser,
        'ctrip': ctrip_parser.ctrip_parser,
        'elong': elong_parser.elong_parser,
        'expedia': expedia_parser.expedia_parser,
        'hotels': hotels_parser.hotels_parser,
        'hoteltravel': hoteltravel_parser.hoteltravel_parser,
        'hrs': hrs_parser.hrs_parser,
        'cheaptickets': expedia_parser.expedia_parser,
        'orbitz': expedia_parser.expedia_parser,
        'travelocity': expedia_parser.expedia_parser,
        'ebookers': expedia_parser.expedia_parser,
        'tripadvisor': tripadvisor_parser.tripadvisor_parser,
        'ctripcn': ctrip_cn_parser.ctrip_cn_parser,
        'hilton': hilton_parser.hilton_parser
    }
    if source not in function_dict.keys():
        raise TypeCheckError('Error Parser Source        with source %s   url %s ' % (source, url))

    parser = function_dict[source]
    result = parser(content, url, other_info)

    # key words check
    # logger.info('map_info  ++++++++    %s' % result.map_info)
    # if key_is_legal(result.map_info) and key_is_legal(result.address):
    if not key_is_legal(result.map_info):
        if retry_count > 5:
            if not key_is_legal(result.address):
                raise TypeCheckError(
                    'Error map_info and address NULL        with parser %ss    url %s' % (parser.func_name, url))
            google_map_info = google_get_map_info(result.address)
            if not key_is_legal(google_map_info):
                raise TypeCheckError(
                    'Error google_map_info  NULL        with parser %ss    url %s' % (parser.func_name, url))
            result.address = google_map_info
        else:
            raise TypeCheckError('Error map_info NULL        with parser %ss    url %s' % (parser.func_name, url))

    if key_is_legal(result.hotel_name) or key_is_legal(result.hotel_name_en):
        logger.info(result.hotel_name + '  ----------  ' + result.hotel_name_en)
    else:
        raise TypeCheckError(
            'Error hotel_name and hotel_name_en Both NULL        with parser %s    url %s' % (parser.func_name, url))

    if result.source == 'booking':
        # if not key_is_legal(result.hotel_name):
        #     raise TypeCheckError('booking has no hotel name        with parser %s    url %s' % (parser.func_name, url))
        # if not key_is_legal(result.hotel_name_en):
        #     raise TypeCheckError('booking has no hotel name en        with parser %s    url %s' % (parser.func_name, url))
        if not key_is_legal(result.img_items):
            raise TypeCheckError('booking has no img        with parser %s    url %s' % (parser.func_name, url))

    if result.source == 'hotels':
        if not key_is_legal(result.img_items):
            raise TypeCheckError('hotels has no img        with parser %s    url %s' % (parser.func_name, url))

    # if result.grade in ('NULL', '-1', ''):
    #     raise TypeError('Error Grade NULL')

    result.continent = part

    # expedia 五个源设置 source
    result.source = source

    # result 中 grade 修复
    if result.grade == 'NULL':
        result.grade = -1

    # 酒店全部字段繁体转简体
    keys = ['hotel_name', 'hotel_name_en', 'brand_name', 'address', 'service', 'description', 'accepted_cards',
            'check_in_time', 'check_out_time']

    for key in keys:
        if not getattr(result, key):
            setattr(result, key, 'NULL')
        setattr(result, key, tradition2simple(getattr(result, key).decode()))

    return result


if __name__ == '__main__':
    import requests

    source = 'booking'
    # url = 'http://www.hrs.com/web3/hotelData.do?activity=photo&singleRooms=0&doubleRooms=1&adults=2&children=0&availability=true&hotelnumber=100'
    # url = 'https://www.expedia.cn/h6935892.Hotel-Information'
    # url = 'http://www.booking.com/hotel/th/baan-siripornchai.zh-cn.html?aid=376390;label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-11455299683%3Alp9061505%3Ali%3Adec%3Adm;sid=1ed4c8a52860a4f5a93489f7b31a8863;checkin=2017-08-03;checkout=2017-08-04;ucfs=1;highlighted_blocks=206274801_98817269_2_0_0;all_sr_blocks=206274801_98817269_2_0_0;room1=A%2CA;hpos=4;dest_type=city;dest_id=-3255732;srfid=7078e96d0aca48337ba20a54f0a96429386a2fcfX4;from=searchresults;highlight_room=#hotelTmpl'
    url = 'http://www.booking.com/hotel/th/fondness.zh-cn.html?aid=376390;label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-11455299683%3Alp9061505%3Ali%3Adec%3Adm;sid=1ed4c8a52860a4f5a93489f7b31a8863;checkin=2017-08-03;checkout=2017-08-04;ucfs=1;highlighted_blocks=202844501_94738597_2_0_0;all_sr_blocks=202844501_94738597_2_0_0;room1=A%2CA;hpos=1;dest_type=city;dest_id=-3255732;srfid=7078e96d0aca48337ba20a54f0a96429386a2fcfX1;from=searchresults;highlight_room=#hotelTmpl'
    source = 'expedia'
    url = 'https://www.expedia.com.hk/cn/Savannah-Hotels-Best-Western-Savannah-Historic-District.h454.Hotel-Information'
    other_info = {
        'source_id': 'test',
        'city_id': 'test'
    }
    url = 'http://www.booking.com/hotel/it/cuba-marebello.zh-cn.html'
    source = 'agoda'

    source = 'elong'
    url = 'http://ihotel.elong.com/117200/'

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    parse_hotel(content, url, other_info, source, 'test')
