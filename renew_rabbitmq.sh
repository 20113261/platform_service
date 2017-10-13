#!/usr/bin/env bash

/usr/sbin/rabbitmqctl add_user hourong 1220
/usr/sbin/rabbitmqctl set_user_tags hourong administrator
/usr/sbin/rabbitmqctl add_vhost celery
/usr/sbin/rabbitmqctl set_permissions -p celery hourong ".*" ".*" ".*"

/usr/sbin/rabbitmqctl add_vhost data_insert
/usr/sbin/rabbitmqctl set_permissions -p data_insert hourong ".*" ".*" ".*"

/usr/sbin/rabbitmqctl add_vhost task_info
/usr/sbin/rabbitmqctl set_permissions -p task_info hourong ".*" ".*" ".*"