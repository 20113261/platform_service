#coding:utf-8
# @Time    : 2018/5/30
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : git_supervisor.py
# @Software: PyCharm

#该脚本请在本地解释器下运行！不应使用远程开发机运行。

def git_source(task_name):
    task = '_'.join(task_name.split('_')[-4:-1])
    with open('supervisor_model.conf', 'r') as file:
        content = file.read()
    print content
    content = content.format(task, task)
    file_name = 'supervisor_conf/' + task + '.conf'
    with open(file_name, 'w') as file:
        file.write(content)


if __name__ == '__main__':
    git_source('detail_hotel_hilton_20180531')
