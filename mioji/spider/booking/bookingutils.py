#!/bin/env python
#encoding=UTF8
'''
Created on 2016年9月14日

@author: dujun
'''
import re

def check_is_breakfast_free(text):
    '''
    @return: True if breakfast is free;False otherwise
    @param text: 
    
    '''
    pattern = r'(?<!不)(包括|包含|(?<!包)含).*早餐'
    r = re.search(pattern, text)
    return r != None