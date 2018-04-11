#!/usr/bin/env python
#-*- coding:utf8 -*-

import re
import sys
import json
import os
import math
reload (sys)
sys.setdefaultencoding('utf8')

dept_idCp = re.compile('a1=([^&]+)&')
dest_idCp = re.compile('a2=(\w+)')
modeCp = re.compile('mode=([^&]+)&')
city_modeCp = re.compile('type=([^&]+)')

def parseRouteDataTraffic(routesJson):

    result_json = {}
    return_bool = False
    for i in range(len(routesJson)):
        try:
            if "legs" not in routesJson[i] or len(routesJson[i]["legs"]) < 1:
                print "parse %d google data no legs"%(i)
                continue
            firstLegsJson = routesJson[i]["legs"][0]
            dist = str(firstLegsJson['distance']['value'])
            time = str(firstLegsJson['duration']['value'])
            if "steps" not in firstLegsJson or len(firstLegsJson["steps"]) < 1:
                print "parse %d google data no steps"%(i)
                continue
            stepsJson = firstLegsJson["steps"]
            #过滤只有步行和驾车的公共交通数据
            no_transit = True
            for step in stepsJson:
                if "WALKING" == step["travel_mode"] or "DRIVING" == step["travel_mode"]:
                    continue
                no_transit = False
            if no_transit:
                continue
            result_json["dist"] = dist
            result_json["time"] = time
            result_json["order"] = str(i)
            result_json["route"] = json.dumps(routesJson[i])
            return_bool = True
            break
        except Exception,ex:
            print "parse %d routes google data error"%(i)
            continue
    if not return_bool:
        return ""
    return json.dumps(result_json)

def parseRouteData(routesJson):

    result_json = {}
    return_bool = False
    for i in range(len(routesJson)):
        try:
            if "legs" not in routesJson[i] or len(routesJson[i]["legs"]) < 1:
                print "parse %d google data no legs"%(i)
                continue
            firstLegsJson = routesJson[i]["legs"][0]
            dist = str(firstLegsJson['distance']['value'])
            time = str(firstLegsJson['duration']['value'])
            result_json["dist"] = dist
            result_json["time"] = time
            result_json["order"] = str(i)
            result_json["route"] = json.dumps(routesJson[i])
            return_bool = True
            break
        except Exception,ex:
            print "parse %d routes google data error"%(i)
            continue
    if not return_bool:
        return ""
    return json.dumps(result_json)

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
    routesJson = dataJson["routes"]
    if traffic_type == 2:
        final_result = parseRouteDataTraffic(routesJson)
    else:
        final_result = parseRouteData(routesJson)
    return final_result,index_key,info_key
