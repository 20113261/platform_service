# coding=utf-8
import MySQLdb


def loadCityInfo():
    conn = MySQLdb.connect(host='10.10.111.62', user='reader', charset='utf8', passwd='miaoji1109', db='base_data')
    cursor = conn.cursor()

    sql = "select id,map_info,continent from city"

    cursor.execute(sql)

    datas = cursor.fetchall()

    cid2map = {}

    # 北美洲,南美洲,大洋洲城市距离放宽
    special_city = set()
    for data in datas:
        if None in data:
            continue

        cid = data[0]
        cand_map = data[1]
        continent = data[2]

        try:
            cand_lgt, cand_lat = cand_map.strip().split(',')
            cid2map[cid] = (float(cand_lgt), float(cand_lat))
        except Exception as e:
            continue

        if continent in [u'北美洲', u'南美洲', u'大洋洲']:
            special_city.add(cid)

    cursor.close()
    conn.close()

    return cid2map, special_city


if __name__ == '__main__':
    city2map, special_city = loadCityInfo()

    # print city2map
    print special_city