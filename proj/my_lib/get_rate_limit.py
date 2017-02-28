import pandas
from sqlalchemy import create_engine


def get_rate_limit():
    engine = create_engine('mysql+pymysql://hourong:hourong@10.10.180.145/Task')
    s = pandas.read_sql('select task_name,rate_limit from RateLimit', engine)
    return pandas.Series(s.rate_limit.values, index=s.task_name).to_dict()


if __name__ == '__main__':
    print get_rate_limit()
