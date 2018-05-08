#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
@Time : 17/5/24 下午3:38
@Author : Li Ruibo

'''
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re
import json, urllib, random
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight
from mioji.common.task_info import Task

# 关闭神烦的warning
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

seat_dict = {'ECO':'经济舱','BUS':'商务舱','FST':'头等舱','PEC':'超级经济舱'}
class_code_dict = {'E': 'ECO', 'B': 'BUS', 'F': 'FST', 'P': 'PEC'}

USER_AGENTS = filter(lambda x: x.strip(),'''
Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60
Opera/8.0 (Windows NT 5.1; U; en)
Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50

Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0
Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10

Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2 

Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11
Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16

Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36
Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko


Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11

Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER
Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER) 
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)" 

Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)
Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E) 

Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0
Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0) 

Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36

Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36

Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5

Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5

Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5
Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5

Mozilla/5.0 (Linux; U; Android 2.2.1; zh-cn; HTC_Wildfire_A3333 Build/FRG83D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1
Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1

MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1

Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10

Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13

Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+

Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0

Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124

Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)

UCWEB7.0.2.37/28/999

NOKIA5700/ UCWEB7.0.2.37/28/999

Openwave/ UCWEB7.0.2.37/28/999

Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999]
'''.split('\n'))
LENGTH = len(USER_AGENTS)

class SkyscannerRoundFlightSpider(Spider):
    source_type = "skyscannerFlight"
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    def __init__(self, task=None):
        super(SkyscannerRoundFlightSpider,self).__init__(task)


    def targets_request(self):
        pass

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def first_request():
            main_page_url = 'https://www.tianxun.com/'
            return {'req': {'url': main_page_url, 'headers': '', 'method': 'get'},
                    'data': {'content_type': 'string'},
                    'user_handler': [self.__get_info_from_first_page]
                    }
        @request(retry_count=5, proxy_type=PROXY_REQ)
        def second_request():
            dept_city, dest_city, dept_day, dest_day = self.task.content.split('&')
            self.user_datas['dept_day'] = '-'.join([dept_day[:4],dept_day[4:6],dept_day[-2:]])
            self.user_datas['dest_day'] = '-'.join([dest_day[:4],dest_day[4:6],dest_day[-2:]])
            self.user_datas['dest_city_code'] = dest_city
            self.user_datas['dept_city_code'] = dept_city
            url = 'https://www.tianxun.com/flight/ajax_flightCity.php?keyword={city_code}&jsoncallback=jQuery171032138597924270407_1495615018669&_=1495615036743'
            return [{'req': {'url': url.format(city_code=dept_city), 'headers': '', 'method': 'get'},'data': {'content_type': 'string'},'user_handler': [self.__get_dep_city]},
                    {'req': {'url': url.format(city_code=dest_city), 'headers': '', 'method': 'get'}, 'data': {'content_type': 'string'},'user_handler': [self.__get_dist_city]}
                   ]

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def get_cookies():
            '''
            D_IID
            D_UID
            D_ZID
            D_ZUID 
            D_HID
            D_SID
            :return: 
            '''
            url1 = 'https://www.tianxun.com/ga.729321.js' # get pid
            url2 = 'https://www.tianxun.com/ga.729321.js?PID=1AEE13A2-C955-30B6-B8E3-3EF40A8E9B22'
            post_data_url2 = '''p={"proof":"12:1495695297943:sRWIZssWHQwCCm1GfM1W","fp2":{"userAgent":"Mozilla/5.0(Macintosh;IntelMacOSX10_11_3)AppleWebKit/537.36(KHTML,likeGecko)Chrome/58.0.3029.110Safari/537.36","language":"zh-CN","screen":{"width":1920,"height":1080,"availHeight":977,"availWidth":1920},"timezone":8,"indexedDb":true,"addBehavior":false,"openDatabase":true,"cpuClass":"unknown","platform":"MacIntel","doNotTrack":"1","plugins":"ChromePDFViewer::::application/pdf~pdf;ChromePDFViewer::PortableDocumentFormat::application/x-google-chrome-pdf~pdf;NativeClient::::application/x-nacl~,application/x-pnacl~;WidevineContentDecryptionModule::EnablesWidevinelicensesforplaybackofHTMLaudio/videocontent.(version:1.4.8.970)::application/x-ppapi-widevine-cdm~","canvas":{"winding":"yes","towebp":true,"blending":true,"img":"cea445f1b1ca33d2bbb58bdc6c5b276f405a2080"},"webGL":{"img":"ec1ac927598cc32e395530f37437b13e3d7a4bdc","extensions":"ANGLE_instanced_arrays;EXT_blend_minmax;EXT_disjoint_timer_query;EXT_frag_depth;EXT_shader_texture_lod;EXT_sRGB;EXT_texture_filter_anisotropic;WEBKIT_EXT_texture_filter_anisotropic;OES_element_index_uint;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_compressed_texture_s3tc;WEBKIT_WEBGL_compressed_texture_s3tc;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBKIT_WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;WEBKIT_WEBGL_lose_context","aliasedlinewidthrange":"[1,1]","aliasedpointsizerange":"[1,255.875]","alphabits":8,"antialiasing":"yes","bluebits":8,"depthbits":24,"greenbits":8,"maxanisotropy":16,"maxcombinedtextureimageunits":80,"maxcubemaptexturesize":16384,"maxfragmentuniformvectors":1024,"maxrenderbuffersize":16384,"maxtextureimageunits":16,"maxtexturesize":16384,"maxvaryingvectors":15,"maxvertexattribs":16,"maxvertextextureimageunits":16,"maxvertexuniformvectors":1024,"maxviewportdims":"[16384,16384]","redbits":8,"renderer":"WebKitWebGL","shadinglanguageversion":"WebGLGLSLES1.0(OpenGLESGLSLES1.0Chromium)","stencilbits":0,"vendor":"WebKit","version":"WebGL1.0(OpenGLES2.0Chromium)","vertexshaderhighfloatprecision":23,"vertexshaderhighfloatprecisionrangeMin":127,"vertexshaderhighfloatprecisionrangeMax":127,"vertexshadermediumfloatprecision":23,"vertexshadermediumfloatprecisionrangeMin":127,"vertexshadermediumfloatprecisionrangeMax":127,"vertexshaderlowfloatprecision":23,"vertexshaderlowfloatprecisionrangeMin":127,"vertexshaderlowfloatprecisionrangeMax":127,"fragmentshaderhighfloatprecision":23,"fragmentshaderhighfloatprecisionrangeMin":127,"fragmentshaderhighfloatprecisionrangeMax":127,"fragmentshadermediumfloatprecision":23,"fragmentshadermediumfloatprecisionrangeMin":127,"fragmentshadermediumfloatprecisionrangeMax":127,"fragmentshaderlowfloatprecision":23,"fragmentshaderlowfloatprecisionrangeMin":127,"fragmentshaderlowfloatprecisionrangeMax":127,"vertexshaderhighintprecision":0,"vertexshaderhighintprecisionrangeMin":31,"vertexshaderhighintprecisionrangeMax":30,"vertexshadermediumintprecision":0,"vertexshadermediumintprecisionrangeMin":31,"vertexshadermediumintprecisionrangeMax":30,"vertexshaderlowintprecision":0,"vertexshaderlowintprecisionrangeMin":31,"vertexshaderlowintprecisionrangeMax":30,"fragmentshaderhighintprecision":0,"fragmentshaderhighintprecisionrangeMin":31,"fragmentshaderhighintprecisionrangeMax":30,"fragmentshadermediumintprecision":0,"fragmentshadermediumintprecisionrangeMin":31,"fragmentshadermediumintprecisionrangeMax":30,"fragmentshaderlowintprecision":0,"fragmentshaderlowintprecisionrangeMin":31,"fragmentshaderlowintprecisionrangeMax":30},"touch":{"maxTouchPoints":0,"touchEvent":false,"touchStart":false},"video":{"ogg":"probably","h264":"probably","webm":"probably"},"audio":{"ogg":"probably","mp3":"probably","wav":"probably","m4a":"maybe"},"fonts":"ArialUnicodeMS;GillSans;HelveticaNeue"},"cookies":1,"setTimeout":0,"setInterval":0,"appName":"Netscape","platform":"MacIntel","syslang":"zh-CN","userlang":"zh-CN","cpu":"","productSub":"20030107","plugins":{"0":"WidevineContentDecryptionModule","1":"ChromePDFViewer","2":"NativeClient","3":"ChromePDFViewer"},"mimeTypes":{"0":"WidevineContentDecryptionModuleapplication/x-ppapi-widevine-cdm","1":"application/pdf","2":"NativeClientExecutableapplication/x-nacl","3":"PortableNativeClientExecutableapplication/x-pnacl","4":"PortableDocumentFormatapplication/x-google-chrome-pdf"},"screen":{"width":1920,"height":1080,"colorDepth":24},"fonts":{"0":"HoeflerText","1":"Times","2":"Monaco","3":"Georgia","4":"TrebuchetMS","5":"Verdana","6":"AndaleMono","7":"Monaco","8":"CourierNew","9":"Courier"}}
Name
ga.729321.js
ga.729321.js?PID=1AEE13A2-C955-30B6-B8E3-3EF40A8E9B22
ads?gdfp_req=1&correlator=2628728269826788&output=json_html&callback=googletag.impl.pubads.callbackProxy1&impl=fifs&json_a=1&eid=108809103,21060003,21060233&sc=1&sfv=1-0-8&iu_parts=24268069,tianxun.com,flights_funnel,day_view,right,left,Top,Bottom,inline&enc_prev_ius=/0/1/2/3/4,/0/1/2/3/5,/0/1/2/3/6,/0/1/2/3/7,/0/1/2/3,/0/1/2/3/8&prev_iu_szs=120x600|160x600,120x600|160x600,300x250|300x600,300x250|300x600,468x60|728x90,1024x66&eri=32&cust_params=cc=economy&children=0&odate=05-2017&idate=&dairp=gyy&dcity=chia&dctry=us&isreturn=true&lang=ZH&oairp=urc&ocity=curc&octry=cn&trafficsplit=&triptype=holiday&origin=%E4%B9%8C%E9%B2%81%E6%9C%A8%E9%BD%90&destination=%E8%8A%9D%E5%8A%A0%E5%93%A5%E5%8A%A0%E9%87%8C&dates=5%E6%9C%8829%E6%97%A5%20%E5%91%A8%E4%B8%80%20-%206%E6%9C%8830%E6%97%A5%20%E5%91%A8%E4%BA%94&cookie=ID=ff6d0f6fa916742d:T=1495683159:S=ALNI_MaG9dyNyvqTtppnJIHMqUvIUCvy9Q&abxe=1&lmt=1495695304&dt=1495695304893&frm=20&biw=906&bih=865&oid=3&adxs=1130,-270,680,680,-9,-9&adys=161,161,161,801,-9,-9&adks=3890871510,1816209342,4211233874,1657630092,1314831367,4157416049&gut=v2&ifi=1&u_tz=480&u_his=3&u_h=1080&u_w=1920&u_ah=977&u_aw=1920&u_cd=24&u_nplug=4&u_nmime=5&u_sd=1&flash=0&url=https://www.tianxun.com/intl-round-curc-gyy.html?depdate=2017-05-29&rtndate=2017-06-30&cabin=Economy&adult=1&child=0&infant=0&dssz=19&icsg=2483945472&mso=8&std=0&vrg=119&vrp=119&ga_vid=518926188.1495683160&ga_sid=1495695305&ga_hid=706182712
imgad?id=CICAgKDLl7j0aRCgARjYBDIIDbmKTtqwPmU
imgad?id=CICAgKDLl7yYaRCgARjYBDII0T9iwuet2Kg
imgad?id=CICAgKDLj-6JrQEQrAIY2AQyCHFjKJKvXw1Z
view?xai=AKAOjsuJ3DOwBA01Tpv7T_ctY6HOfUW5HL40NGLCXk0QfL7oNK8DBjBS2i5RbnnWPY2bl11JE9byoQp18_7wUs4gex15_e188Y1zgAOTry9F7kPEaxyokj-E4LJwyB9Nup0hugNRwV21ZsGdbcdkMeVXSp5LnPutBI4O9sHR3ti-nAGBR4uNssHoUiebSBV5G27S-s04OIFMyQKAHs1a8bbuRLrT4TTNzwVabwZGX3X-rA0IXK4IGtjaNwu0ptaTsoB8ubUxWE28ZAf1NweTZz22cweUDw&sig=Cg0ArKJSzKb6mC1wJcEeEAE&adurl=
view?xai=AKAOjstUll6czXaYxJK8KnUcsxBNPo3mrfQPZQqfcvyoxXQBkybJflj63dd778HGtHpGTKLAWSbHtJKuWMMXIP_DcasqOOhYtDYeMx5SA_r5RsDKyGaFH7N9o9TiRckOozTdiHiZZhiELvgRnU2BOmx6aw43uSfsuVmVfgJlkxm1HuurjyRd6ByJ1QqvlrOnWUPxeuS3JAUprTfeBOuaMW7zJ-DiacPD312rmuQgeUogm7taDOHWDLIRRi5bXJR18_8VhYKCckKBN283El_8KRyllEly&sig=Cg0ArKJSzFDT4f_nX9yPEAE&adurl=
imgad?id=CICAgKDLh8WSShABGAEyCNGV-JzdO363
ga.729321.js?PID=1AEE13A2-C955-30B6-B8E3-3EF40A8E9B22
'''
        @request(retry_count=5, proxy_type=PROXY_REQ)
        def third_request():
            '''
            get sessionKey, token from html
            :return: 
            '''
            adults = 1
            cabinClass = 'Economy'
            user_data = self.user_datas
            url = 'https://www.tianxun.com/intl-round-{dept_city_code_4}-{dest_city_code_4}.html?depdate={depdate}&rtndate={rtndate}&cabin={cabin}&adult={adult}&child=0&infant=0'
            url = url.format(dept_city_code_4=user_data['dept_city_code_full'],dest_city_code_4=user_data['dest_city_code_full'],depdate=user_data['dept_day'],rtndate=user_data['dest_day'],cabin=cabinClass,adult=adults)
            flight_search_state = 'depCityCode::{depCityCode_4}&dstCityCode::{dstCityCode_4}&departDate::{departDate}&returnDate::{returnDate}&isRtn::1&prefDirect::0&cabinClass::{cabinClass}&adult::1&child::0&infant::0&isIntl::1;'
            flight_search_state = flight_search_state.format(depCityCode_4=user_data['dept_city_code_full'],dstCityCode_4=user_data['dest_city_code_full'],
                                                             departDate=user_data['dept_day'],returnDate=user_data['dest_day'],cabinClass=cabinClass,adult=adults)
            flight_search_state = urllib.quote(flight_search_state)
            mixpanel = urllib.quote('"distinct_id": "15c3da9d3c216c-0f213422d53908-3065750a-1fa400-15c3da9d3c33db","$initial_referrer":"{url}" ,"$initial_referring_domain": "www.tianxun.com"'.format(url=url))

            cookie = '''
            D_IID=7E660979-4383-3E12-B8B3-D6CB54121A10; 
            D_UID=2DF6074A-C4D0-3FC3-9BAB-167296434B93; 
            D_ZID=3543E274D-60C2-36DC-A1E7-78A83D2AD954; 
            D_ZUID=64670C48-D0DF-30F6-B0F7-C92D5291C095; 
            D_HID=280F211D-0C00-3520-AAFB-A8A3E93F2106; 
            D_SID=36.110.118.57:X4SYc9r3FA50c6wv/ZPA/WfFaaOuimNy/tXNau4bDJw; 
            geoCountryCode=CN; 
            SSSessionID={SSSession}; 
            sessionid={sessionid}; 
            fCabin={fCabin}; 
            fDepDate={dept_day}; 
            fRtnDate={dest_day}; 
            fDepCityCode={depCityCode_4}; 
            fDstCityCode={dstCityCode_4}; 
            fRoundType=2; 
            fDirect=0; 
            sessionid={sessionid}; 
            visitorid=1495683157516.17236;
            mp_2434748954c30ccc5017faa456fa3d38_mixpanel={mixpanel};
            '''.format(SSSession=user_data.get('SSSessionID',''),sessionid=user_data.get('sessionid',''),fCabin=user_data.get('fCabin',cabinClass),dept_day=user_data.get('dept_day',''),
                       dest_day=user_data.get('dest_day', ''),depCityCode_4=user_data.get('dept_city_code_full',''),dstCityCode_4=user_data.get('dest_city_code_full',''),
                       mixpanel='{' + mixpanel + '};')

            header = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip,deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cache-Control': 'no-cache',
                'DNT': 1,
                'Upgrade-Insecure-Requests': 1,
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'www.tianxun.com',
                'Cookie': cookie,
                'Referer' : 'https://www.tianxun.com/',
                'User-Agent':USER_AGENTS[random.randint(0,LENGTH)],
            }

            return {'req': {'url': url, 'headers': header, 'method': 'get'},'data': {'content_type': 'string'},'user_handler': [self.__get_info_from_main_html]}
        @request(retry_count=5, proxy_type=PROXY_REQ, binding=['flight'])
        def last_request():
            adults = 1
            cabinClass = 'Economy'
            page_num = 1
            user_data = self.user_datas
            flight_search_state='depCityCode::{depCityCode}&dstCityCode::{dstCityCode}&departDate::{departDate}&returnDate::{returnDate}&isRtn::1&prefDirect::0&cabinClass::{cabinClass}&adult::1&child::0&infant::0&isIntl::1;'
            flight_search_state = urllib.quote(flight_search_state)
            url = 'https://www.tianxun.com/flight/ajax_intl_list_v3.php?sessionKey={sessionKey}&token={token}&page={pageNum}&' \
                  'tripType=RT&sort=0&depCityCode={depCityCode}&dstCityCode={destCityCode}&departDate={departDate}' \
                  '&returnDate={returnDate}&abtest=0&_=1495617866156'
            url = url.format(depCityCode=user_data['dept_city_code'],destCityCode=user_data['dest_city_code'],
                             departDate=user_data['dept_day'],returnDate=user_data['dest_day'],
                             sessionKey=user_data['session_key'],token=user_data['token'],cabin=cabinClass,adult=adults, page_num=page_num)
            cookie = '''
                       D_IID=7E660979-4383-3E12-B8B3-D6CB54121A10; 
                       D_UID=2DF6074A-C4D0-3FC3-9BAB-167296434B93; 
                       D_ZID=543E274D-60C2-36DC-A1E7-78A83D2AD954; 
                       D_ZUID=64670C48-D0DF-30F6-B0F7-C92D5291C095; 
                       D_HID=280F211D-0C00-3520-AAFB-A8A3E93F2106; 
                       D_SID=36.110.118.57:X4SYc9r3FA50c6wv/ZPA/WfFaaOuimNy/tXNau4bDJw; 
                       geoCountryCode=CN; 
                       SSSessionID={SSSession}; 
                       sessionid={sessionid}; 
                       fCabin={fCabin}; 
                       fDepDate={dept_day}; 
                       fRtnDate={dest_day}; 
                       fDepCityCode={depCityCode_4}; 
                       fDstCityCode={dstCityCode_4}; 
                       fRoundType=2; 
                       fDirect=0; 
                       sessionid={sessionid}; 
                       visitorid=1495683157516.17236
                        '''.format(SSSession=user_data.get('SSSession',''),sessionid=user_data.get('sessionid',''),fCabin=user_data.get('fCabin',cabinClass),dept_day=user_data.get('dept_day',''),
                       dest_day=user_data.get('dest_day', ''),depCityCode_4=user_data.get('dept_city_code_full',''),dstCityCode_4=user_data.get('dest_city_code_full',''))

            header = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip,deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cache-Control': 'no-cache',
                'DNT': 1,
                'Upgrade-Insecure-Requests': 1,
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'www.tianxun.com',
                'Cookie': cookie,
                'Referer': user_data['url_third'],
                'User-Agent': USER_AGENTS[random.randint(0,LENGTH)]
            }

            return {'req': {'url': url, 'headers': header, 'method': 'get'},'data': {'content_type': 'string'}}

        yield first_request
        yield second_request
        yield third_request
        yield last_request

    def __get_info_from_first_page(self, req, data):
        self.__get_cookies(req['resp'])


    def __get_dep_city(self, req, data):
        self.__get_cookies(req['resp'])
        resp = req['resp']
        country_info = re.search('\[\[.*\]\]', resp.content)
        country_info = country_info.group()
        self.user_datas['dept_city_code_full'] = json.loads(country_info)[0][0]
        pass

    def __get_dist_city(self, req, data):
        self.__get_cookies(req['resp'])

        resp = req['resp']
        country_info = re.search('\[\[.*\]\]', resp.content)
        country_info = country_info.group()
        self.user_datas['dest_city_code_full'] = json.loads(country_info)[0][0]
        pass

    def parse_Flight(self, req, data):
        pass


    def __get_cookies(self,resp):
        cookies = resp.cookies.items()
        for each_cookie in cookies:
            self.user_datas[each_cookie[0]] = each_cookie[1]


    def __get_info_from_main_html(self, req, data):
        self.user_datas['url_third'] = req['req']['url']
        from lxml import html
        dom_tree = html.fromstring(data.decode('utf-8'))
        target = dom_tree.xpath('.//script/text()')
        target = filter(lambda x: 'sessionKey' in x and 'token' in x, target)[0].strip()
        p = '\{\"cabinClass\".*\"abtest\"\:0\}'
        res = re.findall(p, target)[0]
        target_dict = json.loads(res)
        self.user_datas['session_key'] = target_dict['sessionKey'] # get sessionKey
        self.user_datas['token'] = target_dict['token'] # get token

if __name__ == '__main__':
    task = Task()
    task.content = 'URC&HKG&20170702&20170714'
    task.source = 'skyscannerround'
    import httplib
    from mioji.common.task_info import Task
    from mioji.common import spider
    from mioji.common.utils import simple_get_socks_proxy
    spider.get_proxy = simple_get_socks_proxy
    # task.ticket_info = {
    #     "ret_flight_no": "TK1724_TK72",
    #     "ret_dept_time": "20170325_19:00",
    #     "env_name": "offline",
    #     "ret_seat_type": "经济舱|经济舱",
    #     "scene": "pay",
    #     "v_count": 1,
    #     "qid": "1484278907171",
    #     "dest_time": "20170317_13:40",
    #     "v_seat_type": "E",
    #     "seat_type": "经济舱|经济舱",
    #     "flight_no": "TK73_TK1725",
    #     "dept_time": "20170316_23:10",
    #     "pay_method": "mioji",
    #     "ret_dest_time": "20170326_16:55",
    #     "md5": "6bacb08e725ddd248c681aa2e047f1fd"
    # }

    task.source = "skyscannerround"

    httplib.HTTPConnection.debuglevel = 1
    httplib.HTTPSConnection.debuglevel = 1
    # 执行流程：
    # 1. 配置好task, Spider根据task初始化相应的参数
    # 2. 重写targets_request方法
    #   2.1 定义抓取链，并返回
    # 3. 调用基类crawl进行抓取
    #   3.1
    spider = SkyscannerRoundFlightSpider(task)
    spider.crawl()
    print spider.result
