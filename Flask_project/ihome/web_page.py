# coding=utf-8

"""静态页面视图函数"""
# 导包
from flask import Blueprint, current_app, make_response, sessions
from flask_wtf import csrf

# 创建静态页面蓝图
html = Blueprint('html', __name__)

@html.route("/<regex('.*'):file_name>")
def html_file(file_name):

    if not file_name:
        file_name = "index.html"

    if file_name != "favicon.ico":
        file_name = "html/" + file_name


    csrf_token = csrf.generate_csrf()
    respone = make_response(current_app.send_static_file(file_name))

    respone.set_cookie("csrf_token", csrf_token)

    return respone

# TODO

# 启动
if __name__ == '__main__':
    pass