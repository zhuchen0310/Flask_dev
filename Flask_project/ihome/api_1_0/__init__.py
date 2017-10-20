# -*- coding:utf-8 -*-

"""版本初始化文件"""

# 导包
from flask import Blueprint

api = Blueprint('api', __name__)

from . import verifycode, profile, house
# import verifycode
# import profile
# TODO

# 启动
if __name__ == '__main__':
    pass