# coding:utf-8


class CtripGrouptravel:
    def __init__(self):
        self.source_type = "Ctirp|vacation"    # OK
        self.pid = "gty+yyyMMdd+number"
        self.pid_3rd = ""
        self.first_image = ""
        self.sid = ""
        self.ccy = ""
        self.feature = ""
        self.dest = []
        self.dept_city = []
        self.extra_traffic = 0
        self.extra_city = []
        self.name = ""  # 产品名称 OK
        self.date = ""  # 出发日期 OK
        self.set_name = ""  # 套餐名称（线路）OK
        self.set_id = ""  # 套餐ID OK
        self.star_level = 1  # 行程星级 OK
        self.time = 0  # 行程天数（日）OK
        self.highlight = ""  # 产品亮点
        self.confirm = 0  # 预定确认方式，默认给0 OK
        self.sell_date_late = ""  # 最晚可售日期
        self.book_pre = 0  # 提前预定天数，0表示不限
        self.tag = ""  # 特色标签ID 给空 OK
        self.image_list = []  # 轮播图列表 OK
        self.rec = ""  # 产品经理推荐内容 OK
        self.stat = 0   # 录入审核状态 OK
        self.hotel = {"desc": "", "plans": []}  # 参考酒店信息  plans里是这样的{"name": "NULL", "name_en": "NULL", "addr": "NULL", "intro": "NULL", "img": "NULL"}多个字典  OK
        self.expense = [{"type": 0, "title": "", "content": ""}, {"type": 1, "title": "", "content": ""},
                        {"type": 2, "title": "", "content": ""}]  # 费用说明  OK
        self.other = [{"title": "pre_info", "content": ""}, {"title": "visa_info", "content": ""}]  # 其他说明 OK
        self.disable = 0  # OK
        self.single_room = float(0.0)  # 单房差  OK
        self.tourist = []  # 不同人员类型的详细价格和库存，没有可以给空 OK
        self.tour_stat = 0  # 成团状态，0：未成团， 1：已成团 OK
        self.ctime = ""  # 爬取时间戳  OK
        self.route_day = []  # 行程介绍  OK
        # [{"city": {"id": "NULL", "name": "NULL"}, "desc": "NULL", "detail": [{"type": "0", "stime": "NULL", "dur": 0, "name": "NULL", "desc": "NULL", "image_list": []}]}]
        self.is_multi_city = "no"
        self.multi_city = []
        self.dept = ""
        self.ptid = "ptid"
        self.child_standard = ""

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results



