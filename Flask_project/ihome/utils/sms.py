# coding=utf-8

"""发送短信业务逻辑"""

# 导包
from ihome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

_accountSid = '8aaf07085f004cdb015f0b3c98c30547'
# 说明：主账号，登陆云通讯网站后，可在控制台首页中看到开发者主账号ACCOUNT SID。

_accountToken = 'f518266510dc4cd4809f43b01843c36d'
# 说明：主账号Token，登陆云通讯网站后，可在控制台首页中看到开发者主账号AUTH TOKEN。

_appId = '8aaf07085f004cdb015f0b3c9908054b'
# 请使用管理控制台中已创建应用的APPID。

_serverIP = 'sandboxapp.cloopen.com'
# 说明：请求地址，生产环境配置成app.cloopen.com。

_serverPort = '8883'
# 说明：请求端口 ，生产环境为8883.

_softVersion = '2013-12-26'  # 说明：REST API版本号保持不变。

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


class CCP(object):
    """发送短信的辅助类"""
    def __new__(cls, *args, **kwargs):
        """
        判断是否存在类属性 _instance, _instance是类CCP的唯一对象，单例模式

        :param args:
        :param kwargs:
        :return:
        """
        if not hasattr(CCP, '_instance'):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            cls._instance.rest = REST(_serverIP, _serverPort, _softVersion)
            cls._instance.rest.setAccount(_accountSid, _accountToken)
            cls._instance.rest.setAppId(_appId)
            return cls._instance

    def send_template_sms(self, to, datas, temp_id):
        """
        短信发送模板
        :param to:  接收手机号
        :param datas: 内容数据 格式为数组，
        :param temp_id: 模板id
        :return: 成or 失败
        """
        result = self.rest.sendTemplateSMS(to, datas, temp_id)
        # 如果发送短信成功，返回的字典数据result中的statuCode字段值为‘000000’
        if result.get('statusCode') == '000000':
            return 0    # 成功
        else:
            return -1   # 失败


        # 启动
if __name__ == '__main__':
    ccp = CCP()
    ret = ccp.send_template_sms('15513979101', ['1234', 5], 1)
    print ret