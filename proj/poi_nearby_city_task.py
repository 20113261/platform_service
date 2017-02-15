from .celery import app
from my_lib.GetPoiNearByCity.poi_nearby_city_task import insert_db, get_nearby_city
from my_lib.BaseTask import BaseTask
from my_lib.task_module.task_func import update_task


@app.task(bind=True, base=BaseTask, max_retries=3)
def poi_nearby_city_task(self, poi_id, poi_city_id, poi_map_info, **kwargs):
    try:
        nearby_city = get_nearby_city(poi_id=poi_id, poi_city_id=poi_city_id, poi_map_info=poi_map_info)
        print insert_db((poi_id, poi_city_id, nearby_city))
        update_task(kwargs['task_id'])
    except Exception as exc:
        self.retry(exc=exc)
