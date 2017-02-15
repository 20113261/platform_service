# ServicePlatform

## 开发环境

 
    python2.7.12

## 部署


    pip install -r requirements.txt

## 依赖服务


    nfs
    
   
   
## 使用

### start.sh:


    sh start.sh 启动单一 slave
    远程启动, 配置 ssh-key 后
    ssh root@ip地址 "sh /your path/start.sh
    

### kill.sh:


    sh kill.sh 结束单一 slave
    远程结束: 配置 ssh-key 后
    ssh root@ip地址 "sh /your path/start.sh


### init_task.sh:


    sh init_task.sh 开始分发任务，监控程序会调用此脚本发部分
    
### supervisor_start.sh

    sh supervisor_start.sh 守护程序守护的脚本，用于拉起 slave

### check_status.sh

    sh check_status.sh 查看 slave 心跳，用于将监控程序将僵尸程序重启