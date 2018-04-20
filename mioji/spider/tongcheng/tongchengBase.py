#coding:utf-8
cabin = {"Y": "经济舱", "S": "超值经济舱", "C": "公务舱", "F": "头等舱"}
FOR_FLIGHT_DATE = '%Y%m%d%H%M'
changesTypes = {'0': '客票全部未使用', '1': '客票部分使用', '2': 'NoShow起飞前退票', '3': 'NoShow起飞后退票'}
changesStatuss = {'T': '不可退票', 'H': '有条件退票', 'F': '免费退票', 'E': '异常【包含未获取不到结果或异常等情况】【公布运价拦截'}
refundTypes = {'0': '起飞前改期', '1': '起飞后改期', '2': 'NoShow起飞前改期', '3': 'NoShow起飞后改期'}
refundStatuss = {'T': '不可改期', 'H': '有条件改期', 'F': '免费改期', 'E': '异常【包含未获取不到结果或异常等情况】【公布运价拦截'}

flight_type = {
    'flight': '1',
    'flightround': '2',
    'flightmulti': '3',
}