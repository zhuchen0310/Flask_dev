# coding=utf-8

"""发送短信业务逻辑"""

# 导包
from ihome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

accountSid = '8aaf07085f004cdb015f0b3c98c30547'
# 说明：主账号，登陆云通讯网站后，可在控制台首页中看到开发者主账号ACCOUNT SID。

accountToken = 'f518266510dc4cd4809f43b01843c36d'
# 说明：主账号Token，登陆云通讯网站后，可在控制台首页中看到开发者主账号AUTH TOKEN。

appId = '8aaf07085f004cdb015f0b3c9908054b'
# 请使用管理控制台中已创建应用的APPID。

serverIP = 'sandboxapp.cloopen.com'
# 说明：请求地址，生产环境配置成app.cloopen.com。

serverPort = '8883'
# 说明：请求端口 ，生产环境为8883.

softVersion = '2013-12-26'  # 说明：REST API版本号保持不变。

'''
def sendTemplateSMS(to, datas, tempId):
    # 初始化REST SDK
    rest = REST(serverIP, serverPort, softVersion)
    rest.setAccount(accountSid, accountToken)
    rest.setAppId(appId)

    result = rest.sendTemplateSMS(to, datas, tempId)
    for k, v in result.iteritems():
        if k == 'templateSMS':
            for k, s in v.iteritems():
                print '%s:%s' % (k, s)
        else:
            print '%s:%s' % (k, v)
'''


        # 启动
if __name__ == '__main__':
    pass