# Api文档
见 RE4A Web Services Integration Workshop 3 PTP Products v4.pptx

# 请求
先构造一个字典，使用`dict_to_xml`方法将字典转换为xml，打api请求。

# 错误
错误尽量都存放在`error_case`中，通过解析返回xml数据的code和description来确定对应错误。