from proj.tasks import booking_comment
import celery

mioji_host = {
    '10.10.246.28': 'cp01.uc.spider',
    '10.10.242.216': 'cp02.uc.spider',
    '10.10.245.15': 'cp03.uc.spider',
    '10.10.236.79': 'crawlplatform_1.uc.off',
    '10.10.232.57': 'crawlplatform_2.uc.off',
    '10.10.240.2': 'crawlplatform_3.uc.off',
    '10.10.215.238': 'crawlplatform_4.uc.off',
    '10.10.218.176': 'crawlplatform_5.uc.off',
}

if __name__ == '__main__':
    res = celery.current_app.control.inspect().ping()
    ip_set = set()
    for key in res.keys():
        ip_set.add(key.replace('celery@', '').replace('-', '.'))

    for ip, host in mioji_host.items():
        if ip not in ip_set:
            print host
