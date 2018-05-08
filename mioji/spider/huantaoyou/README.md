# 欢逃游
##爬虫入口  
spider，必须要参数 
```python
    task.ticket = {'wanle': 对方id}
```
返回数据
```json
{
    "view_ticket": {
        "info": {
            "FYNBH": "餐饮、自费项目、个人花费及其他未提及费用。", 
            "TGSM": "<ul><li>我们提供退款服务，细则如下：</li><li>退订政策：1、消费日期前7天（大于等于7天），可全额退款。</li><li>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;2、消费日期前7天内（大于等于4天），可退款70%。</li><li>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;3、消费日前4天内（小于4天），无法退款。</li><li>改订政策：抱歉，此商品暂不支持订单修改服务。</li><li>（注：促销期间购买的商品，一律不支持退改。）</li></ul><br>", 
            "JDJS": "景点图片: http://img.huantaoyou.com/CT/AU/231/dc450735a00247fd9bc2d98069f90283.png|景点介绍: 海洋世界（Sea World）位于黄金海岸，全部引进黄金海岸的纯天然海水，是澳洲最大的海洋公园，可泛舟水上，也可搭乘直升飞机空中遨游，乐趣无穷！<br><br>海洋世界有很多大型水族馆区，各种稀奇海洋生物畅游其中；陆生动物也是包罗万象，应有尽有。公园有各种高端游乐设施，如云霄飞车和海盗船等。这里的表演精彩纷呈，最经典的当属滑水和海豚海狮表演。<br>", 
            "FWYY": "Non-Service", 
            "FYBH": "黄金海岸海洋世界门票。", 
            "SYRQ": "年龄限制 (14 - 99)", 
            "GMXZ": "最多预定人数: 无限制|最少预订人数: 无限制|提前预定天数: 4", 
            "GDXX": "备注:请您下单时，在订单备注处留下您的邮箱地址，以便接收电子票，感谢合作！|取票时间:营业时间均可。|营业时间:园区内9:30-17:30；游乐设施10:00-17:00。<br>全年无休，圣诞节不开放，4.25澳新军团日当天13:30开馆。<br>|消费地址:SeaWorld Drive,Main Beach,Gold Coast,QLD,Australia|其它:海洋世界里卖的食物都很贵，建议自备午餐或零食。<br>|出示证件:护照。|取票地点:Sea World正门的6号柜台。", 
            "CPXX": "看最美海洋，玩水上乐园|<div>海洋世界里的海洋动物有鲸鱼、鲨鱼、海豚、海狮和五颜六色的热带鱼……还有十分精彩的动物表演！公园内的水上乐园也非常好玩，终极飞车是它的王牌项目！除此之外，还有乘坐游轮、直升飞机环岸游项目供你选择……包你玩得尽兴，HIGH个不停！</div><ul><li>澳洲最大的海洋公园</li><li>经典的海豚海狮表演</li><li>超级好玩的水上乐园</li></ul>||http://img.huantaoyou.com/PUB/AU/AU00014/8b627ff09b03449cb4ebecf289950ea2.png||title: 海洋世界5大震馆法宝|description: <blockquote></blockquote>· 迷人的鲨鱼湾<br>· 乘坐终极飞车<br>·&nbsp;北极熊海岸探险<br>·&nbsp;经典的海豚海狮表演<br>· 在企鹅馆观看呆萌的王企鹅和金图企鹅<br>|image_url: http://img.huantaoyou.com/PUB/AU/AU00014/e2099a41fe2545f69f1eb3a05c06772e.png|title: 海豚、鲨鱼任你选！|description: 海洋世界连续4次被评为澳洲最受欢迎旅游胜地，它为企鹅、海豚、鲨鱼等海洋动物都设有主题馆。<br><br>在海洋馆，你能跟着饲养员一起训海豚、喂鲨鱼……有木有惊悚到？除了可以抚摸海豚，还能近距离接触大鲨鱼哦！<br>|image_url: http://img.huantaoyou.com/PUB/AU/AU00014/405d51d6b4ef4b88b0a026d9926e3978.png|title: 海狮领衔表演秀开幕了！|description: · 海狮纷纷化身敏捷的特警侦探，为大家带来滑稽有趣的可爱演出。<br>· 世界一流的水上摩托特技演员，表演水上摩托特技超极限演出。<br>· 儿童互动体验节目十分欢快，非常逗趣！<br>· 欢乐的海豚们已经准备好了，快坐好看SHOW吧！<br>· 海绵宝宝也来表演啦，带来了顶呱呱的水上演出和响当当的主题船。<br>· 互动表演：在《多拉的好朋友探险记》现场表演时，可以加入他们载歌载舞！<br>|image_url: http://img.huantaoyou.com/PUB/AU/AU00014/9f210e94fe6a465b9a8124632084ce98.png|title: 水上乐园之终极飞车|description: 海洋世界在夏季开设了一系列的水上活动，如海盗船、终极飞车。在你看得尽兴之余，还能玩得过瘾！<br><br>终极飞车是海洋世界的王牌项目，来到海洋世界的朋友一定不要错过哦！呼啸而过的飞车，留下一串惊天地泣鬼神的尖叫声，想想就知道多刺激了！|image_url: http://img.huantaoyou.com/PUB/AU/AU00014/26caf89070ae4a128a81e24c9662b72b.png|", 
            "PQSYSM": "票券类型:消费确认函|取票时间:营业时间均可。|取票地点:Sea World正门的6号柜台。|<div>您预定成功后，我们会把《消费确认函》发送到您的邮箱中；您须打印《消费确认函》并携带，至消费地点时出示即可。</div><div>注：请务必注意您的电子邮箱地址正确，并打印、携带《消费确认函》。</div>", 
            "ZSAP": null, 
            "TJKD": "既能看海豚海狮表演，又能游玩水上乐园，还有黄金海岸空中环游项目！", 
            "CKXC": "<div>打车、包车、自驾：沿Monaco St向西，从环岛3驶出，继续沿Monaco St前行，左转进入Gold Coast Hwy/State Route 2，再右转进入Waterways Dr，继续前行上Macarthur Parade，在环岛处进入Seaworld Dr，即可到达，费时15分钟。</div><div>公交线路：乘坐705路公交车即可到达，费时29分钟。注：周一至周日： 06:00–22:30，每15分钟一趟。建议乘坐公交车前往。</div>", 
            "ZYSX": "<div>1、景点采用一票制，景点内游乐项目包含在景点门票里面。</div><div>2、景点中涉及自费项目，游客可以自行选择，票面价格不包含自费项目。</div><div>3、因景点工作原因或天气原因造成游客无法进入景点，景点全额退票；若因游客自身原因造成无法按时进入景点，门票恕不退还。</div><div>4、如遇特殊情况，公司有权根据澳洲法规调整票价。</div><div>5、购买年票和VIP卡的游客可以免费进入。</div><div></div>", 
            "YCAP": null
        }, 
        "ename": null, 
        "id_3rd": "10013", 
        "first_img": "http://img.huantaoyou.com/PUB/AU/AU00014/IM_4086646727994658982a6be606e0c642.png", 
        "city_id": 1059, 
        "ref_poi": "v223210", 
        "jiesong_type": "0", 
        "poi_mode": 16384, 
        "enter_pre": "0", 
        "times": [
            {
                "dur": -3, 
                "t": "17:30"
            }, 
            {
                "dur": -3, 
                "t": "13:30"
            }
        ], 
        "img_list": [
            "http://img.huantaoyou.com/CT/AU/231/dc450735a00247fd9bc2d98069f90283.png", 
            "http://img.huantaoyou.com/PUB/AU/AU00014/IM_4086646727994658982a6be606e0c642.png", 
            "http://img.huantaoyou.com/PUB/AU/AU00014/8b627ff09b03449cb4ebecf289950ea2.png", 
            "http://img.huantaoyou.com/PUB/AU/AU00014/e2099a41fe2545f69f1eb3a05c06772e.png", 
            "http://img.huantaoyou.com/PUB/AU/AU00014/405d51d6b4ef4b88b0a026d9926e3978.png", 
            "http://img.huantaoyou.com/PUB/AU/AU00014/9f210e94fe6a465b9a8124632084ce98.png", 
            "http://img.huantaoyou.com/PUB/AU/AU00014/26caf89070ae4a128a81e24c9662b72b.png", 
            "http://img.huantaoyou.com/inc/images/ORDER_NO_EXCHANGE.jpg"
        ], 
        "tag": "门票", 
        "__type": "view_ticket", 
        "book_pre": "4", 
        "tickets": {
            "info": [
                {
                    "num": 1, 
                    "type": 0
                }, 
                {
                    "num": 0, 
                    "type": 1
                }, 
                {
                    "num": 0, 
                    "type": 2
                }, 
                {
                    "num": 0, 
                    "type": 3
                }
            ], 
            "ticket_3rd": "2199", 
            "id_3rd": "10013", 
            "ccy": "RMB", 
            "name": "成人", 
            "min": "0", 
            "max": "0", 
            "price": 256, 
            "agemax": 99, 
            "times": [
                {
                    "dur": -3, 
                    "t": "17:30"
                }, 
                {
                    "dur": -3, 
                    "t": "13:30"
                }
            ], 
            "__type": "tickets_fun", 
            "book_pre": "4", 
            "sid": 1, 
            "date": "2017-08-01~2018-01-01", 
            "agemin": 14, 
            "ticketType": 1, 
            "enter_pre": "0"
        }, 
        "jiesong_poi": {
            "addr": "接送地址: None|接送时间:None", 
            "coord": "等待编写"
        }, 
        "date": "2017-08-01~2018-01-01", 
        "map_info": "153.425516,-27.957300", 
        "name": "黄金海岸海洋世界门票"
    }, 
    "tour_ticket": null, 
    "play_ticket": null, 
    "activity_ticket": null
```
四个key，如果有数据，key 对应的value不为null。tickets_fun放在产品的返回字段里面了

## poi匹配
poi匹配走另外一个套逻辑，但是写的很乱，推荐重写。主要逻辑在merge_data里面。

## 关于数据融合的问题
因为需要跟我们库里的数据对的上，推荐这个流程独立出来。之前这个流程处于没人管的状态。只是单纯地把数据存在了mongodb里面，以后可能要
做成一个流程。

## 数据库地址
mongodb 
```
host=10.10.114.244
port=27017
user=root
pasword=miojiqiangmima
```
mysql暂时使用的是spiderbase里面的tmp

## 自己跑数据的流程
run.py会读取data里面的wanle，并且把数据入库