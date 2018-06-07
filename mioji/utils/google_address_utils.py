#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月20日

@author: dujun
'''


def find_google_region(address_info):
    '''
    :param address_info: mapapi geocode 返回:$.address_info
    :return: 返回区域节点，没有返回None
    '''
    _length = len(address_info)
    for i in xrange(1, _length + 1):
        if 'country' in address_info[-i].get('types', []):
            country_index = -(i + 1)
            
            if -country_index <= _length:
                return address_info[country_index]
    
    return None

def find_google_region_by_addressnode(address_node):
    '''
    :param address_info: mapapi geocode 返回:$.address_info
    :return: 返回区域节点，没有返回None
    '''
    address_info = address_node.get('address_components', [])
    _length = len(address_info)
    for i in xrange(1, _length + 1):
        if 'country' in address_info[-i].get('types', []):
            country_index = -(i + 1)
            
            if -country_index <= _length:
                return address_info[country_index]
    
    return None

def find_google_countrynode(address_node):
    '''
    :param address_info: mapapi geocode 返回:$.address_info
    :return: 返回区域节点，没有返回None
    '''
    address_info = address_node.get('address_components', [])
    _length = len(address_info)
    for i in xrange(1, _length + 1):
        if 'country' in address_info[-i].get('types', []):
            return address_info[-i]
    
    return None
    
if __name__ == '__main__':
    print len(('51319', '21071', '10143', '40163', '20234', '20237', '20327', '11397', '50290', '51149', '20419', '12253', '21289', '10142', '50453', '50569', '51280', '30260', '12815', '13013', '20921', '21339', '12991', '13022', '50520', '12078', '30082', '30303', '12408', '11340', '12131', '50943', '12331', '21346', '51216', '12159', '13273', '30255', '20932', '51246', '21428', '21436', '20281', '50271', '30164', '30221', '20279', '20280', '50043', '50897', '12725', '12797', '20972', '50475', '50880', '13012', '20352', '12458', '20638', '20673', '20342', '21127', '21155', '21161', '21173', '50560', '50621', '51119', '20877', '13482', '30231', '11975', '20420', '13324', '51357', '51105', '12863', '21030', '21031', '13289', '10093', '20982', '11904', '10157', '10147', '50065', '50473', '51272', '13214', '13270', '12147', '13184', '51407', '11870', '10081', '12030', '10686', '13226', '12834', '12048', '20313', '21350', '20417', '11211', '20945', '21028', '13427', '20935', '50687', '51223', '51331', '21011', '13083', '11862', '20909', '12938', '11008', '11108', '10912', '20380', '20675', '20952', '11792', '10322', '12152', '20272', '51181', '20232', '20626', '20643', '12357', '21135', '20360', '20672', '50648', '12074', '12162', '20946', '40447', '50133', '50743', '10697', '21351', '50434', '30181', '30182', '12259', '13251', '40292', '11915', '50399', '10827', '12109', '20944', '50674', '11962', '12372', '10134', '10198', '12982', '20985', '50522', '13028', '10965', '11404', '50627', '50725', '50071', '11913', '40027', '40307', '40314', '20908', '50161', '30208', '51244', '21159', '20286', '51355', '10227', '30276', '12166', '13500', '12013', '50355', '21079', '10284', '50883', '51141', '51310', '20275', '20989', '21074', '10218', '21165', '12325', '21397', '10239', '12041'))
        