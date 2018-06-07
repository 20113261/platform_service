#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月17日

@author: dujun
'''

def generate_page_post_data(jdata):
    try:
       relist = jdata.get('SearchCriteria','')
       s_m_id = relist.get('','SearchMessageID')
       relist.get('', '')
       s_type = relist.get('SearchType', '')
       ob_id = relist.get('ObjectID', '')
       f_hotel_name = relist.get('Filters', {}).get('HotelName', '')
       f_price_min = relist.get('Filters', {}).get('PriceRange',{}).get('Min', '')
       f_price_max = relist.get('Filters', {}).get('PriceRange', {}).get('Max', '')
       f_review_min = relist.get('Filters', {}).get('ReviewScoreMin', {})
       f_filter_size = relist.get('Filters',{}).get('Size', '')
       # rate_p_id = '' if relist['RateplanIDs'][0] is None else relist['RateplanIDs'][0]
       total_hotel = relist.get('TotalHotels', '')
       plat_id = relist.get('PlatformID', '')
       current_date = relist.get('CurrentDate', '')
       search_id =  relist.get('SearchID', '')
       city_id =  relist.get('CityId', '')

       latitude = relist.get('Latitude', '')
       longitude = relist.get('Longitude', '')
       radius = relist.get('Radius', '')
       page_number = 1
       page_size = relist.get('PageSize', '')
       sort_type = relist.get('SortType', '')
       is_sort_change = relist.get('IsSortChanged', '')
       review_tra_type = relist.get('ReviewTravelerType', '')
       point_max_pro = relist.get('PointsMaxProgramId', '')
       poll_times = relist.get('PollTimes', '')
       city_name = relist.get('CityName', '')
       obj_name = relist.get('ObjectName', '')
       country_name = relist.get('CountryName', '')
       country_id = relist.get('CountryId', '')
       is_allow_ye_search = relist.get('IsAllowYesterdaySearch', '')
       culture_info = relist.get('CultureInfo', '')
       unava_hotel_id = relist.get('UnavailableHotelID', '')
       is_enable_aps = relist.get('IsEnableAPS', '')
       addition_exp_prius = relist.get('AdditionalExperiments', {}).get('PRIUS', '')
       seleted_hotel_id = relist.get('SeletedHotelId', '')
       has_filter = relist.get('HasFilter', '')
       land_Pheader_bannerurl = relist.get('LandingParameters', {}).get('HeaderBannerUrl', '')
       land_Pfooter_bannerurl = relist.get('LandingParameters', {}).get('FooterBannerUrl', '')
       land_Pselected_hotelid = relist.get('LandingParameters', {}).get('SelectedHotelId', '')
       land_Pcityid = relist.get('LandingParameters', {}).get('LandingCityID', '')
       new_ssr_search_type = relist.get('NewSSRSearchType', '')
       is_wysiwyp = relist.get('IsWysiwyp', '')
       request_price_view = relist.get('RequestPriceView', '')
       final_price_view = relist.get('FinalPriceView', '')
       map_type = relist.get('MapType', '')
       is_show_mobi_appprice = relist.get('IsShowMobileAppPrice', '')
       is_aps_peek = relist.get('IsAPSPeek', '')
       check_inculture_datatext = relist.get('CheckInCultureDateText', '')

       check_outculture_datatext = relist.get('CheckOutCultureDateText', '')
       adults = relist.get('Adults', '')
       childrens = relist.get('Children', '')
       rooms = relist.get('Rooms', '')
       check_in = relist.get('CheckIn', '')
       len_of_stay = relist.get('LengthOfStay', '')
       text = relist.get('Text', '')
    except Exception, ex1:
        print('[DEBUG]: ex1---->' +  ex1.message)
        pass
    try:
        post_data = {
            "SearchMessageID": s_m_id,
            "SearchType": s_type,
            "ObjectID": ob_id,
            "Filters[HotelName]": f_hotel_name,
            "Filters[PriceRange][Min]": f_price_min,
            "Filters[PriceRange][Max]": f_price_max,
            'Filters[ReviewScoreMin]': f_review_min,
            'Filters[Size]': f_filter_size,
            # 'RateplanIDs[]': rate_p_id,
            'TotalHotels': total_hotel,
            'PlatformID': plat_id,
            'CurrentDate': current_date,
            'SearchID': search_id,
            'CityId': city_id,
            'Latitude': latitude,
            'Longitude': longitude,
            'Radius': radius,
            'PageNumber': page_number,
            'PageSize': page_size,
            'SortType': sort_type,
            'IsSortChanged': is_sort_change,
            'ReviewTravelerType': review_tra_type,
            'PointsMaxProgramId': point_max_pro,
            'PollTimes': poll_times,
            'CityName': city_name,
            'ObjectName': obj_name,
            'CountryName': country_name,
            'CountryId': country_id,
            'IsAllowYesterdaySearch': is_allow_ye_search,
            'CultureInfo': culture_info,
            'UnavailableHotelID': unava_hotel_id,
            'IsEnableAPS': is_enable_aps,
            'AdditionalExperiments[PRIUS]': addition_exp_prius,
            'SeletedHotelId': seleted_hotel_id,
            'HasFilter': has_filter,
            'LandingParameters[HeaderBannerUrl]': land_Pheader_bannerurl,
            'LandingParameters[FooterBannerUrl]': land_Pfooter_bannerurl,
            'LandingParameters[SelectedHotelId]': land_Pselected_hotelid,
            'LandingParameters[LandingCityID]': land_Pcityid,
            'NewSSRSearchType': new_ssr_search_type,
            'IsWysiwyp': is_wysiwyp,
            'RequestPriceView': request_price_view,
            'FinalPriceView': final_price_view,
            'MapType': map_type,
            'IsShowMobileAppPrice': is_show_mobi_appprice,
            'IsAPSPeek': is_aps_peek,
            'CheckInCultureDateText': check_inculture_datatext,
            'CheckOutCultureDateText': check_outculture_datatext,
            'Adults': adults,
            'Children': childrens,
            'Rooms': rooms,
            'CheckIn': check_in,
            'LengthOfStay': len_of_stay,
            'Text': text
        }
        return post_data
    except Exception,e:
        print('[Debug] : generate_page_post_data---->' + e.message)
        pass