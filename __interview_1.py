#coding:utf-8
# @Time    : 2018/6/2
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : __interview_1.py
# @Software: PyCharm

import sys

#重定向：
# file = open('out.txt', 'a')
#
# print >>file, 'file'
#
# savedStdout = sys.stdout  #保存标准输出流
# with open('out.txt', 'a') as file:
#     sys.stdout = file  #标准输出重定向至文件
#     print 'This message is for file!'
#
# sys.stdout = savedStdout  #恢复标准输出流
# print 'This message is for screen!'

#readlines
with open('_interview_test.py', 'r') as f:
    # a = ''
    # for i in range(1000000):
    #     a += 'a'
    # f.write('\n')
    # f.write(a)
    # f.write('\n')
    # f.write('\n')
    # f.write(a)

    a = f.readlines(1)
    for i in  a:
        print(len(i))



