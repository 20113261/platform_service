FROM centos:centos7

RUN yum -y update; yum clean all &&
    yum -y install epel-release; yum clean all &&
    yum -y install python-pip; yum clean all &&
    yum -y install git gcc geos mysql-devel gpgme-devel libxml2-devel libjpeg-turbo-devel libxslt-devel npm python-devel; yum clean all &&
    pip install --upgrade pip;

# Add your app folder
COPY . /app
WORKDIR /app

# 添加日志文件夹添加修改环境变量
RUN mkdir -p /data/log/service_platform &&
    # 克隆并且打包 Spider 以及老爬虫 slave
#    cd /data &&
#    git config --global credential.helper 'cache --timeout 3600' &&
#    git config --global user.name "hourong" &&
#    export GIT_ASKPASS="miaoji123" &&
#    git clone http://gitlab-ci-token:zEyofj-syMs6VfsiKNeP@gitlab.uc.online/spider_new/Spider.git
#    echo hourong|git clone http:// &&
#    git checkout release_spider;
    export PYTHONPATH=$PYTHONPATH:/app/lib:/data/Spider/src:/data/slave_develop_new/workspace/spider/SpiderClient/bin:/data/slave_develop_new/workspace/spider/SpiderClient/lib &&


# Add your python requirements
RUN pip install -r requirements.txt
CMD python app.py