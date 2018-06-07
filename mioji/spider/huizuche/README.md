## 需求文档 
https://docs.google.com/document/d/1JrF9oPHhisMGoMGV3ZnYkD4HxznLYEJ-nAvjfYWCUYk/edit?usp=sharing
## 惠租车接口文档 
https://drive.google.com/file/d/0B0Pmz1iKwHiLMGZfQWNkZVdKVzA/view?usp=sharing函数
## 函数作用:
md5_key生成sign值，req_post_header生成请求头, get_json为发送请求并返回一个字典形数据
run函数为启动函数，传入字典形post数据，返回一个形如[{{}]每一个字典里都是一个具体的产品信息
```post = {
        'pickupDateTime': '2017-12-22T10:00:00',  # 借入日期
        'returnDateTime': '2017-12-23T10:00:00',  # 返回日期
        'pickupLocationCode': 'LAX',  # 借入机场三字码
        'returnLocationCode': 'LAX',  # 返回机场三字码
    }

