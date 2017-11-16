# !/usr/bin/python
# -*- coding: UTF-8 -*-

from another_semi_automatic import prepare_data_hotel_list_old, prepare_data_daodao_list_hotel_suggestions_city, \
    prepare_data_daodao_list_ota_location, prepare_data_daodao_list_SuggestName, prepare_data_hotel_list_new, \
    prepare_data_qyer_list_ota_location, prepare_data_qyer_list_QyerSuggestCityUrl

def control_hotel(sources, part, priority, cities):
    for source in sources:
        prepare_data_hotel_list_old(source, part, priority, cities)
        prepare_data_hotel_list_new(source, part, priority, cities)

def control_daodao(part, priority, cities):
    for poi_type in ['attr', 'rest']:
        prepare_data_daodao_list_hotel_suggestions_city(poi_type, part, priority, cities)
        prepare_data_daodao_list_ota_location(poi_type, part, priority, cities)
        prepare_data_daodao_list_SuggestName(poi_type, part, priority, cities)

def control_qyer(part, priority, cities):
    prepare_data_qyer_list_QyerSuggestCityUrl(part, priority, cities)
    prepare_data_qyer_list_ota_location(part, priority, cities)


if __name__ == '__main__':
    pass