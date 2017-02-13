# tourico 更新流程

## 请求解析相关函数
`tourico_func.py` 酒店信息相关函数
`tourico_city_func.py` 城市相关函数

## 更新全量的 hotel_id
**数据会存储到 hotel_id_total_test 表中**
`get_hotel_id.py`

## 更新 hotel info
配置 celery 中的 task, 任务函数和启动函数在 `tasks.py` 中


## 更新 city_id
通过提供的对应关系划分酒店的 city_id ,一对多的酒店通过画圈取最近值对应我方的 city_id
`add_city_id.py`
   