#!/usr/bin/env python
# encoding: utf-8

import MySQLdb
import pickle
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


db_config = {"host": "10.10.9.184",
             "user": "root",
             "passwd": "Mioji2016-=",
             "db": "spider_qyer",
             "charset": "utf8"}

task_fn = "qyer_country.pkl"


if __name__ == "__main__":
    db_conn = MySQLdb.connect(**db_config)
    sql = "SELECT id, country_en, country_link FROM country_link;"
    db_cur = db_conn.cursor()
    db_cur.execute(sql)
    ret = db_cur.fetchall()
    task_list = ret
    # for item in ret:

    #     task_id = item[0]
    #     for kw in item[1:]:
    #         if kw is None or kw == "" or kw == "0":
    #             continue
    #         else:
    #             task_list.append((task_id, kw,))
    with open(task_fn, 'w') as task_file:
        pickle.dump(task_list, task_file)
    sys.exit()
    print task_list[0]
    import pdb;pdb.set_trace()
    from pprint import pprint
    pprint(task_list)
