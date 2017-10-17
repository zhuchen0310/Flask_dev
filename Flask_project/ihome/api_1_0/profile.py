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
# 导入七牛云
from ihome.utils.image_storage import storage
# 导入db
from ihome import db
# 导入常量信息
from ihome import constants
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
    获取用户信息
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
    # 校验查询结果
    if not user:
        return jsonify(errno=RET.NODATA, errmsg='无效操作')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='ok', data=user.to_dict())



@api.route('/user/avater', methods=['POST'])
@login_required
def set_user_avater():
    """
    上传用户头像
    :return:
    """
    # 1.获取参数
    user_id = g.user_id
    avater = request.files.get('avater')
    # 2.校验参数
    if not avater:
        return jsonify(errno=RET.PARAMERR, errmsg='未上传图片')
    # 3.读取图片数据
    avater_data = avater.read()
    # 4.上传七牛云
    try:
        image_name = storage(avater_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')
    # 5.存储图片信息到数据库中
    try:
        User.query.filter_by(id=user_id).updata({'avater_url':image_name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片异常')
    # 6.拼接图片的完成路径
    image_url = constants.QINIU_DOMIN_PREFIX + image_name
    # 7.返回前端
    return jsonify(errno=RET.OK, errmsg='ok', data={'avater_url':image_url})


@api.route('/user/name', methods=['PUT'])
@login_required
def change_user_name():
    """
    修改用户信息
    :return:
    """
    # 1.获取参数
    req_data = request.get_json()
    # 2.进一步验证数据完整性
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 3.进一步获取详细参数
    name = req_data.get('name')
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 4.获取用户id
    user_id = g.user_id
    # 5.查询数据库,更新信息
    try:
        User.query.filter_by(id=user_id).updata({'name':name})
        db.session.commit()

    except Exception as e:
        current_app.logger.error(e)
        # 回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='更新数据库失败')

    # 6.更新缓存中用户信息
    session['name'] = name
    # 7.返回结果
    return jsonify(errno=RET.OK, errmsg='ok', data={'name':name})


@api.route('/user/auth', methods=['POST'])
@login_required
def set_user_auth():
    """
    用户实名认证
    :return:
    """
    # 获取用户id
    user_id = g.user_id
    # 获取参数
    user_data = request.get_json()
    # 校验参数
    if not user_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 进一步获取参数信息
    real_name = user_data.get('real_name')
    id_code = user_data.get('id_code')
    # 校验参数完整性
    if not all([real_name, id_code]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    #todo 实际是需要掉第三方验证的

    # 保存数据到数据库
    try:
        User.query.filter_by(id=user_id, real_name=None, id_code=None).update({'real_name':real_name, 'id_code':id_code})
        # 提交
        db.session.commit()

    except Exception as e:
        current_app.logger.error(e)
        # 回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='更新数据库异常')
    # 返回前端结果
    return jsonify(errno=RET.OK, errmsg='ok')



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
    # 获取id
    user_id = g.user.id
    # 查询数据库
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    # 进行参数校验
    if user is None:
        return jsonify(errno=RET.DATAERR, errmsg='无效操作')
    else:
        return jsonify(errno=RET.OK, errmsg='ok', data=user.auth_to_dict())


if __name__ == '__main_':
    pass
