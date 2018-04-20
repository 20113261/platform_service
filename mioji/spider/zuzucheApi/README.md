## 需求文档 
https://docs.google.com/document/d/1gO980hMyadriaBBZ8Rg6he3Ov-EASjbwdFw_HRSFt14/edit#

## 需求参数:
```python
    {
        'pickupDateTime': '2017-12-22T10:00:00',  # 借入日期
        'returnDateTime': '2017-12-23T10:00:00',  # 返回日期
        'pickupLocationCode': 'LAX',  # 借入机场三字码/坐标
        'returnLocationCode': 'LAX',  # 返回机场三字码/坐标
    }
```

## 说明

* 调用租租车文档中的第四个接口，请求报价单信息。
* 需求文档中的 公司描述，取消政策，门店电话字段无法从返回的json中获取

