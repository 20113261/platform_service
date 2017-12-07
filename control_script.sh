#!/usr/bin/env bash

# install supervisor
pssh -h hosts.txt -i 'pip install supervisor'

# config supervisor service
cat hosts.txt|xargs -I host scp supervisord host:/etc/init.d

# update supervisor info
cat hosts.txt|xargs -I host scp supervisord.conf host:/etc

# get free memory
pssh -h hosts.txt -i 'cat /proc/meminfo |grep MemFree'

# restart all running process
ps -aux|grep "celery worker"|grep -v grep|awk '{print $2}'|xargs -I each_pid kill -HUP each_pid

# get all running process pid
/usr/bin/pssh -h /root/hosts.txt -i "ps -aux|grep 'celery worker'|grep -v grep|awk '{print \$2}'"

# restart all running process from master
/usr/bin/pssh -h /root/hosts.txt -i "ps -aux|grep 'celery worker'|grep -v grep|awk '{print \$2}'|xargs -I each_pid kill -HUP each_pid"

# test socks5 proxy
curl --socks5 10.10.233.246:36347 http://www.baidu.com
curl --socks5 10.10.233.246:36347 https://s3.amazonaws.com/expedia-static-feed/United+States+(.com)_Merchant_All.csv.gz

curl --socks5 10.10.233.246:36347 http://pic.qyer.com/album/user/2225/43/Q0tXRx4EY00/index

# install centos environment
pssh -h new_hosts.txt -i 'yum install -y curl-devel gpgme-devel python-devel'

# send requirements.txt
cat new_hosts.txt |xargs -I host scp requirements.txt host:/tmp

# install pycurl
pssh -h new_hosts.txt -i 'pip install -i https://pypi.doubanio.com/simple/ pycurl'

# install requirement
pssh -h new_hosts.txt -i 'pip install -i https://pypi.doubanio.com/simple/ -r /tmp/requirements.txt'

# make dir
pssh -h new_hosts.txt -i 'mkdir /data/log'
pssh -h new_hosts.txt -i 'mkdir /data/log/service_platform'
pssh -h new_hosts.txt -i 'mkdir /data/hourong'

# soft link
pssh -h new_hosts.txt -i 'ln -s /data /search'

# send lib env
cat new_hosts.txt |xargs -I host scp -r lib host:/data/

# kill all slave
pssh -h hosts.txt -i 'sh /data/hourong/ServicePlatform/kill_all.sh'