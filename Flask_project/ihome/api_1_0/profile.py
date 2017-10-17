# -*- coding:utf-8 -*-

"""登录账户业务"""

# 导包
from . import api
# flask包
from flask import request, jsonify, current_app, session, g
# 导入自定义状态码
from ihome.utils.response_code import RET
# 导入re模块
import re
# 导入用户模型
from ihome.models import User
# 导入验证登录装饰器
from ihome.utils.commons import login_required


# TODO

@api.route('/sessions', methods=["POST"])
def login():
    """
    /获取登录参数，mobile, passwd get_json()
    /校验参数存在，进一步获取详细参数信息
    /校验手机号格式
    /查询数据库，验证用户信息存在
    /校验查询结果，检查密码正确性
    /缓存用户信息
    /返回登录结果
    :return:
    """
    user_data = request.get_json()
    if not user_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 进一步验证
    mobile = user_data.get('mobile')
    password = user_data.get('password')
    # 校验参数完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 校验手机号
    if not re.match(r'^1[34578]\d{9}$', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号错误')
    # 查询数据库，验证用户信息
    try:
        user = User.query.filter_by(mobile=mobile).first()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库操作异常')

    # 校验查询结果，检查密码正确性
    if user is None or not user.check_password(password):
        return jsonify(errno=RET.DATAERR, errmsg='用户名或者密码错误')
    # 缓存用户信息
    session['user_id'] = user.id
    session['name'] = mobile
    session['mobile'] = mobile
    # 返回登录结果
    return jsonify(errno=RET.OK, errmsg='OK', data={'user_id': user.id})


@api.route('/session', methods=["DELETE"])
@login_required
def logout():
    """
    退出账户
    /清楚缓存中数据
    :return:
    """
    session.clear()
    return jsonify(errno=RET.OK, errmsg='OK')


@api.route('/user', methods=['GET'])
@login_required
def get_user_info():
    """

    :return:
    """
    # 获取用户id
    user_id = g.user.id
    # 查询数据库，根据用户id查询用户信息
    try:
        user = User.query.filter_by(id=user_id).first()
        # TODO

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')


@api.route('/user/auth', methods=["GET"])
@login_required
def get_user_auth():
    """
    获取用户实名信息
    1/获取用户id
    2/根据用户id，查询数据库
    3/校验查询结果
    4/返回前端。user.auth_to_dict():user.to_dict()
    :return:
    """
    user_id = g.user.id
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if user is None:
        return jsonify(errno=RET.DATAERR, errmsg='无效错误')
    else:
        return jsonify(errno=RET.OK, errmsg='ok', data={'user'})


if __name__ == '__main_':
    pass
