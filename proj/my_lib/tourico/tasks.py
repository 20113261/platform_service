# coding=utf-8
from .tourico_func import queryGetHotelDetailsV3,get_per_data,insert_data

# 任务部分
@app.task(bind=True, max_retries=10, rate_limit='15/s')
def tourico_base_data(self, hotel_id, city_id):
    try:
        hotels = queryGetHotelDetailsV3([hotel_id])
        data = get_per_data(hotels, city_id)
        if not data:
            self.retry()
        print insert_data([data])
    except:
        self.retry()


# 任务分发部分
from tourico_func import get_task_new

for hotel_id in get_task_new():
    tourico_base_data.delay(hotel_id, '')
