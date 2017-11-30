# coding=utf-8

"""此文件配置通用设施，验证装饰器，url正则路由"""

# 导包
import functools
from flask import session, g, jsonify
from werkzeug.routing import BaseConverter
from ihome.utils.response_code import RET


class RegexConverter(BaseConverter):
    """在路由中使用正则表达式进行参数提取的工具"""
    def __init__(self, url_map, *args):
        super(RegexConverter, self).__init__(url_map)
        self.regex = args[0]


def login_required(f):
    """
    验证用户登录的装饰器
    :param f:
    :return:
    """
    # functools让被装饰的函数名称不会改变
    @functools.wraps(f)
    def wrapper(*arges,**kwargs):
        # 从session中获取user_id
        user_id = session.get('user_id')
        if user_id is None:
            return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
        else:
            # 用户已经登录
            g.user_id = user_id
            return f(*arges, **kwargs)
    return wrapper
# TODO

# 启动
if __name__ == '__main__':
    pass
