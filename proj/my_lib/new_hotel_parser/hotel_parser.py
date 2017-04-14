import agoda_parser
import booking_parser
import cheaptickets_parser
import ctrip_parser
import ebookers_parser
import elong_parser
import expedia_parser
import hotels_parser
import hoteltravel_parser
import hrs_parser
import orbitz_parser
import travelocity_parser
from data_obj import DBSession


def parse_hotel(content, url, other_info, source, part):
    function_dict = {
        'agoda': agoda_parser.agoda_parser,
        'booking': booking_parser.booking_parser,
        'ctrip': ctrip_parser.ctrip_parser,
        'elong': elong_parser.elong_parser,
        'expedia': expedia_parser.expedia_parser,
        'hotels': hotels_parser.hotels_parser,
        'hoteltravel': hoteltravel_parser.hoteltravel_parser,
        'hrs': hrs_parser.hrs_parser,
        'cheaptickets': cheaptickets_parser.cheaptickets_parser,
        'orbitz': orbitz_parser.orbitz_parser,
        'travelocity': travelocity_parser.travelocity_parser,
        'ebookers': ebookers_parser.ebookers_parser,
    }
    if source not in function_dict.keys():
        raise TypeError('Error Parser Source')

    parser = function_dict[source]
    result = parser(content, url, other_info)

    # key words check
    if result.map_info in ('NULL', ''):
        raise TypeError('Error map_info NULL')

    if result.address in ('NULL', ''):
        raise TypeError('Error address NULL')

    if result.source == 'booking' and (result.img_items == '' or result.img_items == 'NULL'):
        raise TypeError('booking has no img')

    # if result.grade in ('NULL', '-1', ''):
    #     raise TypeError('Error Grade NULL')

    result.continent = part

    task_finished = False
    session = DBSession()
    session.merge(result)
    session.commit()
    session.close()
    task_finished = True

    return task_finished


if __name__ == '__main__':
    import requests

    source = 'expedia'
    # url = 'http://www.hrs.com/web3/hotelData.do?activity=photo&singleRooms=0&doubleRooms=1&adults=2&children=0&availability=true&hotelnumber=100'
    url = 'https://www.expedia.cn/h6935892.Hotel-Information'
    other_info = {
        'source_id': '6935892',
        'city_id': '10162'
    }

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    parse_hotel(content, url, other_info, source, 'test')
