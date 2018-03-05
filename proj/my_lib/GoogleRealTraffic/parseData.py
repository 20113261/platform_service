#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import json
import gzip
import sys
import datetime
import os
import json
import math
import multiprocessing
import distance_protocol_pb2

reload(sys)
sys.setdefaultencoding('utf8')

# 过滤代码与原因对应关系初始化
filter_map = dict()
filter_map[1] = "type err"
filter_map[-1] = "process  err"
filter_map[20] = "start or dest map err"
filter_map[21] = "walk too long more 10km"
filter_map[3] = "time too long more 5hour"
filter_map[4] = "coor err"
filter_map[5] = "invalid data"
filter_map[6] = "only walk"
filter_map[22] = "info too long"

dept_idCp = re.compile('a1=([^&]+)&')
dest_idCp = re.compile('a2=(\w+)')
# city_idCp = re.compile('cciittyy=([^&]+)')
start_mapCp = re.compile('origin=(\-?\d+\.\d+,\-?\d+\.\d+)&')
dest_mapCp = re.compile('destination=(\-?\d+\.\d+,\-?\d+\.\d+)&')
coorCp = re.compile('(\-?\d+\.\d+,\-?\d+\.\d+)')
htmlCp = re.compile('<[^>]+?>')
modeCp = re.compile('mode=([^&]+)&')
city_modeCp = re.compile('type=([^&]+)')

KOriginShift = 2 * math.pi * 6378137 / 2.0


def LonToMeters(lon, lat):
    mx = lon * KOriginShift / 180.0
    return mx


def LatToMeters(lon, lat):
    my = math.log(abs(math.tan((90 + lat) * math.pi / 360.0))) * KOriginShift / math.pi
    return my


def decodePolydata(content):
    index = 0;
    results = []
    while 1:
        shift = 0
        result = 0
        while 1:
            c = ord(content[index]) - 63
            result |= ((c & 0x1F) << (5 * shift))
            shift += 1
            index += 1
            if c < 0x20:
                break
        if result & 1:
            result = ~result
        result = result >> 1
        tt = result * 0.00001
        results.append(tt)
        if index >= len(content):
            break
    for i in range(len(results)):
        if i == 0:
            continue
        if i == 1:
            continue
        results[i] += results[i - 2]
    ttt = []
    cnt = 0
    last = ''
    str_list = ["0", "0"]
    for i in results:
        cnt += 1
        if cnt % 2:
            str_list[1] = str(i)
        else:
            str_list[0] = str(i)
            str_list.append("0")
            ttt.append(','.join(str_list))
            str_list = ["0", "0"]
            # for i in results:
            #	cnt += 1
            #	if cnt % 2:
            #		last = str(i)
            #	else:
            #		last += ','+str(i)
            #		last += ',0'
            #		ttt.append( last )
            # results = '|'.join(ttt)
            # return results
    return ttt


def processCoorAdd(coor):
    l = coor.strip().split('|')
    k = []
    for i in l:
        k.append(i.split(',')[1] + ',' + i.split(',')[0] + ',0')
    k = '|'.join(k)
    return k


def processCoorAddTransit(coor, n1, n2):
    l = coor.strip().split('|')
    k = []
    for i in range(len(l)):
        if i == 0:
            k.append(l[i].split(',')[1] + ',' + l[i].split(',')[0] + ',' + str(n1))
        elif i == len(l) - 1:
            k.append(l[i].split(',')[1] + ',' + l[i].split(',')[0] + ',' + str(n2))
        else:
            k.append(l[i].split(',')[1] + ',' + l[i].split(',')[0] + ',0')
    k = '|'.join(k)
    return k


def addES_addInfo(pointA, pointB, items, headWalk, destWalk):
    #######     这个函数只适用于公交

    #######     sign_add_S sign_add_E format dict
    #######     key: status,int
    #######          value,int
    #######          time,int

    # items = coords.split('|')
    res = []
    pointAx = pointA.split(',')[0]
    pointAy = pointA.split(',')[1]
    pointBx = pointB.split(',')[0]
    pointBy = pointB.split(',')[1]

    sign_add_S = {}
    sign_add_E = {}
    sign_add_S['status'] = 0
    sign_add_E['status'] = 0

    for i in range(len(items)):
        tx = ''
        ty = ''
        flag = ''
        if '::' in items[i]:
            if len(items[i].split('::')) != 2:
                return -1
            flag = items[i].split('::')[1].strip()
            xy = items[i].split('::')[0]
            if len(xy.split(',')) != 2:
                return -1
            tx = xy.split(',')[0]
            ty = xy.split(',')[1]
        else:
            pieces = items[i].split(',')

            if len(pieces) != 3:
                return '-1'
            tx = pieces[0]
            ty = pieces[1]
            flag = pieces[2].strip()
        if i == 0:
            # 如果coor的坐标列表，第一个坐标跟起始点坐标完全统一的话，判断coor里面的格式问题，补上没有S的问题
            if pointAx == tx and pointAy == ty:
                if flag == 'S':
                    pass
                else:
                    flag = 'S'
                    # 如果coor的坐标列表，第一个坐标跟起始点坐标不统一的话，直接加上一个S的起始坐标，并抹掉之前的S坐标
            else:
                res.append('%s,%s::%s' % (pointAx, pointAy, 'S'))
                sign_add_S['status'] = 1  # 1表示需要添加步行的info段
                sign_add_S['value'] = int(1000 * getDist('%s,%s' % (pointAx, pointAy), '%s,%s' % (tx, ty)))  # 单位是m
                sign_add_S['time'] = int(sign_add_S['value'] / 1.4)
                if headWalk > 0:
                    flag = '0'
                else:
                    flag = '1'

        if i == len(items) - 1:
            # 如果coor的坐标列表，最后一个坐标跟目的地坐标完全统一的话，判断coor里面的格式问题，补上没有E的问题
            if pointBx == tx and pointBy == ty:
                if flag == 'E':
                    pass
                else:
                    flag = 'E'
                    # 如果coor的坐标列表，最后一个坐标跟目的地坐标不统一的话，直接加上一个E的起始坐标，并抹掉之前的E坐标
            else:
                if destWalk > 0:
                    res.append('%s,%s::%s' % (tx, ty, '0'))
                else:
                    res.append('%s,%s::%s' % (tx, ty, '1'))
                res.append('%s,%s::%s' % (pointBx, pointBy, 'E'))
                sign_add_E['status'] = 1
                sign_add_E['value'] = int(1000 * getDist('%s,%s' % (pointBx, pointBy), '%s,%s' % (tx, ty)))
                sign_add_E['time'] = int(sign_add_E['value'] / 1.4)
                continue

                # 添加默认的坐标，或者添加被抹掉SE的起止坐标
        res.append('%s,%s::%s' % (tx, ty, flag))
        # res = '|'.join(res)
    return res, sign_add_S, sign_add_E


def addES(pointA, pointB, items):
    res = []
    pointAx = pointA.split(',')[0]
    pointAy = pointA.split(',')[1]
    pointBx = pointB.split(',')[0]
    pointBy = pointB.split(',')[1]

    for i in range(len(items)):
        tx = ''
        ty = ''
        flag = ''
        if '::' in items[i]:
            if len(items[i].split('::')) != 2:
                print items[i]
                return -1
            flag = items[i].split('::')[1].strip()
            xy = items[i].split('::')[0]
            if len(xy.split(',')) != 2:
                print items[i]
                return -1
            tx = xy.split(',')[0]
            ty = xy.split(',')[1]
        else:
            pieces = items[i].split(',')

            if len(pieces) != 3:
                print items[i]
                return '-1'
            tx = pieces[0]
            ty = pieces[1]
            flag = pieces[2].strip()
        if i == 0:
            # 如果coor的坐标列表，第一个坐标跟起始点坐标完全统一的话，判断coor里面的格式问题，补上没有S的问题
            if pointAx == tx and pointAy == ty:
                if flag == 'S':
                    pass
                else:
                    flag = 'S'
                    # 如果coor的坐标列表，第一个坐标跟起始点坐标不统一的话，直接加上一个S的起始坐标，并抹掉之前的S坐标
            else:
                res.append('%s,%s::%s' % (pointAx, pointAy, 'S'))
                flag = '0'

        if i == len(items) - 1:
            # 如果coor的坐标列表，最后一个坐标跟目的地坐标完全统一的话，判断coor里面的格式问题，补上没有E的问题
            if pointBx == tx and pointBy == ty:
                if flag == 'E':
                    pass
                else:
                    flag = 'E'
                    # 如果coor的坐标列表，最后一个坐标跟目的地坐标不统一的话，直接加上一个E的起始坐标，并抹掉之前的E坐标
            else:
                res.append('%s,%s::%s' % (tx, ty, '0'))
                res.append('%s,%s::%s' % (pointBx, pointBy, 'E'))
                continue
                flag = '0'

                # 添加默认的坐标，或者添加被抹掉SE的起止坐标
        res.append('%s,%s::%s' % (tx, ty, flag))
    return res


def getDegree(fX, fY, sX, sY, tX, tY):
    fX = float(fX);
    fY = float(fY);
    sX = float(sX);
    sY = float(sY);
    tX = float(tX);
    tY = float(tY)
    fXr = LonToMeters(fX, fY);
    fYr = LatToMeters(fX, fY);
    sXr = LonToMeters(sX, sY);
    sYr = LatToMeters(sX, sY);
    tXr = LonToMeters(tX, tY);
    tYr = LatToMeters(tX, tY)
    a = 2 * math.sqrt((fXr - sXr) ** 2 + (fYr - sYr) ** 2) * math.sqrt((tXr - sXr) ** 2 + (tYr - sYr) ** 2)
    b = ((fXr - sXr) ** 2 + (fYr - sYr) ** 2) + ((tXr - sXr) ** 2 + (tYr - sYr) ** 2) - (
        (tXr - fXr) ** 2 + (tYr - fYr) ** 2)
    if a <= 1e-4:
        return 180
    degree = b / a
    grade = 0
    if (degree > 1):
        degree = 1
    if (degree < -1):
        degree = -1
    grade = math.acos(degree) * 180 / 3.1415926
    return grade


def compress(items):
    newitems = list(set(items))
    newitems.sort(key=items.index)
    fx, fy, sx, sy, tx, ty = 0, 0, 0, 0, 0, 0
    degree, times = 0, 0
    newCoords = []
    for i in range(len(newitems)):
        pieces = newitems[i].replace('::', ',', 10000).split(',')
        tx = pieces[0]
        ty = pieces[1]
        flag = pieces[2]
        if i < 2:
            newCoords.append('%s,%s::%s' % (tx, ty, flag))
            fx = sx
            fy = sy
            sx = tx
            sy = ty
            continue
        if flag == '-1' or flag == '0':
            if i >= 2:
                degree = getDegree(fx, fy, sx, sy, tx, ty)
                if degree > 170 or degree < 10:
                    if times < 5:
                        times += 1
                        fx = sx
                        fy = sy
                        sx = tx
                        sy = ty
                        continue
                    else:
                        times = 0
        newCoords.append('%s,%s::%s' % (sx, sy, flag))
        fx = sx
        fy = sy
        sx = tx
        sy = ty
        # newCoords = '|'.join(newCoords)
    return newCoords


def getDist(pointA, pointB):
    PI = 3.1415926
    ER = 6371.004
    radAX = float(pointA.split(',')[0]) * PI / 180
    radAY = float(pointA.split(',')[1]) * PI / 180
    radBX = float(pointB.split(',')[0]) * PI / 180
    radBY = float(pointB.split(',')[1]) * PI / 180
    value = math.cos(radAY) * math.cos(radBY) * math.cos(radBX - radAX) + \
            math.sin(radAY) * math.sin(radBY)
    if value > 1: value = 1.0
    if value < -1: value = -1.0
    value = ER * math.acos(value)
    return value


def reverseCoor(coor):
    p = coor.split(',')
    return '%s,%s' % (p[1], p[0])


def deleteSamePoint(coords):
    # coords = content.strip().split('|')
    templist = []
    last = coords[0]
    sign = 0
    for i in range(1, len(coords)):
        if coords[i].split(',')[0] == last.split(',')[0] and coords[i].split(',')[1] == last.split(',')[1]:
            if last.split(',')[2] == '0' and coords[i].split(',')[2] == '0':
                templist.append(last)
            elif last.split(',')[2] == '0' and coords[i].split(',')[2] != '0':
                templist.append(coords[i])
            elif last.split(',')[2] != '0' and coords[i].split(',')[2] == '0':
                templist.append(last)
            elif last.split(',')[2] != '0' and coords[i].split(',')[2] != '0':
                templist.append(coords[i])
            sign = 1
        else:
            if sign == 1:
                sign = 0
                pass
            else:
                templist.append(last)
        last = coords[i]
    templist.append(last)
    # res = '|'.join(templist)
    return templist


def getCoorPb(coorList, disCoorPb):
    for ll in coorList:
        disCoorMsg = disCoorPb.distance_coor_single_vec.add()
        sub_list = ll.split("::")
        if len(sub_list[-1]) == 0:
            disCoorMsg.flag = 0
        else:
            disCoorMsg.flag = ord(sub_list[-1][0])
        lng_lat = sub_list[0].split(',')
        # 经度
        disCoorMsg.lng = float(lng_lat[0])
        # 纬度
        disCoorMsg.lat = float(lng_lat[-1])


def getInfoPb(infoList, disInfoPb):
    print '|'.join(infoList)
    disInfoPb.brief_introduction = '|'.join(infoList)


def parseDataInterCityDrive(routesJson):
    # transferMessage = distance_protocol_pb2.Transfer_Message()
    # return_bool = False
    # for i in range(len(routesJson)):
    #	try:
    #		if "legs" not in routesJson[i] or len(routesJson[i]["legs"]) < 1:
    #			print "parse %d google data no legs"%(i)
    #			continue
    #		firstLegsJson = routesJson[i]["legs"][0]
    #		dist = int(firstLegsJson['distance']['value'])
    #		time = int(firstLegsJson['duration']['value'])
    #		#城市间驾车
    #		singleMessage = transferMessage.distance_single_vec.add()
    #		singleMessage.dist = dist
    #		singleMessage.time = time
    #		singleMessage.order = i
    #		return_bool = True
    #		break
    #	except Exception,ex:
    #		print "parse %d routes google data error"%(i)
    #		continue
    # if not return_bool:
    #	return ""
    # return transferMessage.SerializeToString()
    transferMessage = distance_protocol_pb2.Transfer_Message()
    return_bool = False
    for i in range(len(routesJson)):
        try:
            infoList = []
            if "legs" not in routesJson[i] or len(routesJson[i]["legs"]) < 1:
                print "parse %d google data no legs" % (i)
                continue
            firstLegsJson = routesJson[i]["legs"][0]
            dist = int(firstLegsJson['distance']['value'])
            time = int(firstLegsJson['duration']['value'])
            # 城市间公交步行驾车
            if "steps" not in firstLegsJson or len(firstLegsJson["steps"]) < 1:
                print "parse %d google data no steps" % (i)
                continue
            stepsJson = firstLegsJson["steps"]
            for step in stepsJson:
                navi = ""
                if (step.has_key('maneuver')):
                    navi = step['maneuver']
                instruction = step['html_instructions']
                instruction = htmlCp.sub('', instruction)
                instruction = instruction.replace('~', ' ')
                instruction = instruction.replace('#', ' ')
                instruction = instruction.replace('\'', '\\\'')
                instruction = instruction.replace('|', ' ')
                navi = navi.replace('~', ' ')
                navi = navi.replace('#', ' ')
                infoList.append(
                    '%s#%s#%s#%s' % (navi, instruction, step['distance']['value'], step['duration']['value']))
            disInfoPb = transferMessage.distance_info_message.add()
            getInfoPb(infoList, disInfoPb)
            singleMessage = transferMessage.distance_single_vec.add()
            singleMessage.dist = dist
            singleMessage.time = time
            return_bool = True
            break
        except Exception, ex:
            print "parse %d routes google data error" % (i)
            continue
    if not return_bool:
        return ""
    return transferMessage.SerializeToString()


def parseDataInnerCityWalk(routesJson, dept_map, dest_map):
    transferMessage = distance_protocol_pb2.Transfer_Message()
    return_bool = False
    for i in range(len(routesJson)):
        try:
            coorList = []
            infoList = []
            if "legs" not in routesJson[i] or len(routesJson[i]["legs"]) < 1:
                print "parse %d google data no legs" % (i)
                continue
            firstLegsJson = routesJson[i]["legs"][0]
            dist = int(firstLegsJson['distance']['value'])
            time = int(firstLegsJson['duration']['value'])
            # 城市内公交步行驾车
            if "steps" not in firstLegsJson or len(firstLegsJson["steps"]) < 1:
                print "parse %d google data no steps" % (i)
                continue
            stepsJson = firstLegsJson["steps"]
            for step in stepsJson:
                # coorList.append(processCoorAdd(decodePolydata(step['polyline']['points'])))
                coorList.extend(decodePolydata(step['polyline']['points']))
                navi = ""
                if (step.has_key('maneuver')):
                    navi = step['maneuver']
                instruction = step['html_instructions']
                instruction = htmlCp.sub('', instruction)
                instruction = instruction.replace('~', ' ')
                instruction = instruction.replace('#', ' ')
                instruction = instruction.replace('\'', '\\\'')
                instruction = instruction.replace('|', ' ')
                navi = navi.replace('~', ' ')
                navi = navi.replace('#', ' ')
                infoList.append(
                    '%s#%s#%s#%s' % (navi, instruction, step['distance']['value'], step['duration']['value']))
            coorList = deleteSamePoint(coorList)
            coorList = addES(dept_map, dest_map, coorList)
            coorList = compress(coorList)
            disCoorPb = transferMessage.distance_coor_message.add()
            disInfoPb = transferMessage.distance_info_message.add()
            getCoorPb(coorList, disCoorPb)
            getInfoPb(infoList, disInfoPb)
            singleMessage = transferMessage.distance_single_vec.add()
            singleMessage.dist = dist
            singleMessage.time = time
            return_bool = True
            break
        except Exception, ex:
            print "parse %d routes google data error" % (i)
            continue
    if not return_bool:
        return ""
    return transferMessage.SerializeToString()


def parseDataInnerCityDrive(routesJson, dept_map, dest_map):
    transferMessage = distance_protocol_pb2.Transfer_Message()
    return_bool = False
    for i in range(len(routesJson)):
        try:
            coorList = []
            infoList = []
            if "legs" not in routesJson[i] or len(routesJson[i]["legs"]) < 1:
                print "parse %d google data no legs" % (i)
                continue
            firstLegsJson = routesJson[i]["legs"][0]
            dist = int(firstLegsJson['distance']['value'])
            time = int(firstLegsJson['duration']['value'])
            # 城市内公交步行驾车
            if "steps" not in firstLegsJson or len(firstLegsJson["steps"]) < 1:
                print "parse %d google data no steps" % (i)
                continue
            stepsJson = firstLegsJson["steps"]
            for step in stepsJson:
                # coorList.append(processCoorAdd(decodePolydata(step['polyline']['points'])))
                coorList.extend(decodePolydata(step['polyline']['points']))
                navi = ""
                if (step.has_key('maneuver')):
                    navi = step['maneuver']
                instruction = step['html_instructions']
                instruction = htmlCp.sub('', instruction)
                instruction = instruction.replace('~', ' ')
                instruction = instruction.replace('#', ' ')
                instruction = instruction.replace('\'', '\\\'')
                instruction = instruction.replace('|', ' ')
                navi = navi.replace('~', ' ')
                navi = navi.replace('#', ' ')
                infoList.append(
                    '%s#%s#%s#%s' % (navi, instruction, step['distance']['value'], step['duration']['value']))
            coorList = deleteSamePoint(coorList)
            coorList = addES(dept_map, dest_map, coorList)
            coorList = compress(coorList)
            disCoorPb = transferMessage.distance_coor_message.add()
            disInfoPb = transferMessage.distance_info_message.add()
            getCoorPb(coorList, disCoorPb)
            getInfoPb(infoList, disInfoPb)
            singleMessage = transferMessage.distance_single_vec.add()
            singleMessage.dist = dist
            singleMessage.time = time
            return_bool = True
            break
        except Exception, ex:
            print "parse %d routes google data error" % (i)
            continue
    if not return_bool:
        return ""
    return transferMessage.SerializeToString()


def parseDataInnerCityTransit(routesJson, dept_map, dest_map):
    transferMessage = distance_protocol_pb2.Transfer_Message()
    return_bool = False
    for i in range(len(routesJson)):
        try:
            coorList = []
            infoList = []
            if "legs" not in routesJson[i] or len(routesJson[i]["legs"]) < 1:
                print "parse %d google data no legs" % (i)
                continue
            firstLegsJson = routesJson[i]["legs"][0]
            dist = int(firstLegsJson['distance']['value'])
            time = int(firstLegsJson['duration']['value'])
            # 城市内公交步行驾车
            if "steps" not in firstLegsJson or len(firstLegsJson["steps"]) < 1:
                print "parse %d google data no steps" % (i)
                continue
            stepsJson = firstLegsJson["steps"]
            n1 = 1
            n2 = 2
            headWalk = 0
            destWalk = 0
            stepIdx = 0
            walk = 0
            drive = 0
            filter_bool = True
            for step in stepsJson:
                stepCount = 1
                stepIdx += 1
                navi = ""
                if (step.has_key('maneuver')):
                    navi = step['maneuver']
                instruction = step['html_instructions']
                instruction = htmlCp.sub('', instruction)
                instruction = instruction.replace('~', ' ')
                instruction = instruction.replace('#', ' ')
                instruction = instruction.replace('\'', '\\\'')
                instruction = instruction.replace('|', ' ')
                navi = navi.replace('~', ' ')
                navi = navi.replace('#', ' ')
                step_dist = step['distance']['value']
                step_time = step['duration']['value']
                if step['travel_mode'] == 'WALKING':
                    walk += step['distance']['value']
                    infoList.append('%s#%s#%s#%s#%s#%s#%s#~#%s#%s' % (
                        'walk', '0', str(step_time), str(step_dist), 'WALK', str(stepCount), '-1~-1', navi,
                        instruction))
                    coorList.extend(decodePolydata(step['polyline']['points']))
                    if stepIdx == 1:
                        headWalk = 1
                    if stepIdx == len(stepsJson):
                        destWalk = 1
                elif step['travel_mode'] == 'DRIVING':
                    drive += step['distance']['value']
                    infoList.append('%s#%s#%s#%s#%s#%s#%s#~#%s#%s' % (
                        'drive', '0', str(step_time), str(step_dist), 'DRIVE', str(stepCount), '-1~-1', navi,
                        instruction))
                    coorList.extend(decodePolydata(step['polyline']['points']))
                    n1 += 2
                    n2 += 2
                else:
                    stepType = step['transit_details']['line']['vehicle']['type'].lower()
                    stepCount = step['transit_details']['num_stops']
                    if stepType in ['bus', 'intercity_bus', 'trolleybus']:
                        stepType = 'bus'
                    elif stepType in ['metro_rail', 'subway', 'tram']:
                        stepType = 'subway'
                    elif stepType in ['monorail', 'heavy_rail', 'commuter_train', 'high_speed_train']:
                        stepType = 'train'
                    elif stepType in ['ferry']:
                        stepType = 'ship'
                    else:
                        print "unkown transit type: " + stepType
                        filter_bool = True
                        break
                    departStop = step['transit_details']['departure_stop']['name']
                    arrivalStop = step['transit_details']['arrival_stop']['name']
                    departStop = departStop.replace('~', ' ')
                    departStop = departStop.replace('#', ' ')
                    departStop = departStop.replace('|', ' ')
                    arrivalStop = arrivalStop.replace('~', ' ')
                    arrivalStop = arrivalStop.replace('#', ' ')
                    arrivalStop = arrivalStop.replace('|', ' ')
                    lineName = ''
                    if (step['transit_details']['line'].has_key('short_name')):
                        lineName = step['transit_details']['line']['short_name']
                    else:
                        lineName = step['transit_details']['line']['name']
                    lineName = lineName.replace('~', ' ')
                    lineName = lineName.replace('#', ' ')
                    lineName = lineName.replace('\'', '\\\'')
                    lineName = lineName.replace('|', ' ')
                    infoList.append('%s#%s#%s#%s#%s#%s#%s#%s~%s#%s#%s' % (
                        stepType, '0', str(step_time), str(step_dist), str(lineName), str(stepCount), '-1~-1',
                        str(departStop), str(arrivalStop), navi, instruction))
                    coorList.extend(decodePolydata(step['polyline']['points']))
                    n1 += 2
                    n2 += 2
                    filter_bool = False
            if filter_bool:
                print "filter_bool"
                continue
            coorList = deleteSamePoint(coorList)

            #######	 sign_add_S sign_add_E format dict
            #######	 key: status,int
            #######		  value ,int
            #######		  time  ,int
            coorList, sign_add_S, sign_add_E = addES_addInfo(dept_map, dest_map, coorList, headWalk, destWalk)
            ##如果在计算出来的起始点跟query里面的出发点不同的话，且加上了S，要把这段步行距离给补上
            if sign_add_S['status'] == 1:
                dist += sign_add_S['value']
                walk += sign_add_S['value']
                time += sign_add_S['time']
                if len(infoList) < 1:
                    print "len(infoList) < 1"
                    continue
                info_filter = infoList[-1].split('#')
                if 'WALK' in infoList[0]:
                    new_info = '%s#%s#%d#%d#%s#%s#%s#~#%s#%s' % (
                        'walk', '0', int(info_filter[2]) + sign_add_S['value'],
                        int(info_filter[3]) + sign_add_S['time'],
                        'WALK', '1', '-1~-1', info_filter[8], info_filter[9])
                    infoList[0] = new_info
                else:
                    new_info = '%s#%s#%d#%d#%s#%s#%s#~#%s#%s' % (
                        'walk', '0', sign_add_S['value'], sign_add_S['time'], 'WALK', '1', '-1~-1', info_filter[8],
                        info_filter[9])
                    new_info_list = []
                    new_info_list.append(new_info)
                    new_info_list.extend(infoList)
                    infoList = new_info_list
                    ##如果在计算出来的终止点跟query里面的终止点不同的话，且加上了E，要把这段步行距离给补上
            if sign_add_E['status'] == 1:
                dist += sign_add_E['value']
                walk += sign_add_E['value']
                time += sign_add_E["time"]
                templist = []
                if len(infoList) < 1:
                    continue
                info_filter = infoList[-1].split('#')
                ##如果交通方式是步行的话
                if 'WALK' in infoList[-1]:
                    new_info = '%s#%s#%d#%d#%s#%s#%s#~#%s#%s' % (
                        'walk', '0', int(info_filter[2]) + sign_add_E['value'],
                        int(info_filter[3]) + sign_add_E['time'],
                        'WALK', '1', '-1~-1', info_filter[8], info_filter[9])
                    infoList[-1] = new_info
                ##如果交通方式不是步行的话
                else:
                    new_info = '%s#%s#%d#%d#%s#%s#%s#~#%s#%s' % (
                        'walk', '0', sign_add_E['value'], sign_add_E['time'], 'WALK', '1', '-1~-1', info_filter[8],
                        info_filter[9])
                infoList.append(new_info)

            coorList = compress(coorList)
            disCoorPb = transferMessage.distance_coor_message.add()
            disInfoPb = transferMessage.distance_info_message.add()
            getCoorPb(coorList, disCoorPb)
            getInfoPb(infoList, disInfoPb)
            singleMessage = transferMessage.distance_single_vec.add()
            singleMessage.dist = dist
            singleMessage.time = time
            singleMessage.walk = walk
            return_bool = True
            break
        except Exception, ex:
            print "parse %d routes google data error" % (i)
            continue
    if not return_bool:
        return ""
    return transferMessage.SerializeToString()


def ParseGoogleData(url, data):
    try:
        dataJson = json.loads(data.strip())
    except Exception, ex:
        print "load google data error"
        return "", "", "", ""
    if "routes" not in dataJson or len(dataJson["routes"]) < 1:
        print "google data no routes"
        return "", "", "", ""
    try:
        city_mode = city_modeCp.findall(url)[0]
        traffic_mode = modeCp.findall(url)[0]
        dept_id = dept_idCp.findall(url)[0]
        dest_id = dest_idCp.findall(url)[0]
    except Exception as ex:
        print "regenx url error"
        return "", "", "", ""

    if traffic_mode == "walking":
        traffic_type = 1
    elif traffic_mode == "driving":
        traffic_type = 0
        if city_mode == "interCity":
            traffic_type = 3
    elif traffic_mode == "transit":
        traffic_type = 2
    else:
        print "traffic_type error"
        return "", "", "", ""
    tmp_key = dept_id + "_" + dest_id + "_" + str(traffic_type)
    index_key = tmp_key + "_0"
    info_key = "info_" + index_key
    coor_key = "coor_" + index_key

    if traffic_type != 3:
        try:
            dept_map = reverseCoor(start_mapCp.findall(url)[0])
            dest_map = reverseCoor(dest_mapCp.findall(url)[0])
        except Exception, ex:
            print "get map error"
            return "", "", "", ""

    routesJson = dataJson["routes"]
    if traffic_type == 0:  # 城市内驾车
        final_result = parseDataInnerCityDrive(routesJson, dept_map, dest_map)
    elif traffic_type == 1:
        final_result = parseDataInnerCityWalk(routesJson, dept_map, dest_map)
    elif traffic_type == 2:
        final_result = parseDataInnerCityTransit(routesJson, dept_map, dest_map)
    elif traffic_type == 3:  # 城市间驾车
        final_result = parseDataInterCityDrive(routesJson)
    # debug###
    debug = distance_protocol_pb2.Transfer_Message()
    debug.ParseFromString(final_result)
    print debug
    for test in debug.distance_single_vec:
    	print test
    #debug###
    # print final_result
    return final_result, index_key, info_key, coor_key
