# coding:utf-8


class Tag:
    def __init__(self):
        self.breakfast = []  # [{"name": "含早餐", "id": "0"},]
        self.hotel_star = []  # [{"key": "一星级", "id": "1"}, {"key": "二星级", "id": "2"]
        self.position = []  # [{"name": "商圈", "tag_list": []}]
        self.others_info = []
        self.city_id = ""
        self.hotel_url = ""

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results
