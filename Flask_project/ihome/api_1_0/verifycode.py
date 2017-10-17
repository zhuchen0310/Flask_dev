# -*- coding:utf-8 -*-

"""发送短信业务逻辑"""

# 导包
# 导入蓝图对象
from . import api
# 导入第三方验证码生成器包
from ihome.utils.captcha.captcha import captcha
# 　导入 redis缓存
from ihome import redis_store
# 导入常量文件
from ihome import constants
# 导入logger
from flask import current_app, jsonify, make_response, request, session
# 导入自定义状态码
from ihome.utils.response_code import RET
# 导入re模块
import re
# 导入用户模型
from ihome.models import User
# 导入随机模块
import random
# 导入云通讯
from ihome.utils import sms
# 导入db
from ihome import db
@api.route('/imagecode/<image_code_id>', methods=['GET'])
def generate_image_code(image_code_id):
    """
    生成图片验证码
    1/调用第三方扩展captcha，实现图片验证码的生成
    2/把图片验证码缓存到redis中
    3/返回图片验证码
    :param image_code_id:
    :return:
    """
    # 调用captcha 生成验证码
    name, text, image = captcha.generate_captcha()
    # 将验证码保存到ｒｅｄｉｓ中
    try:
        redis_store.setex('Imagecode_' + image_code_id, constants.TMAGE_CODE_REDIS_EXPIRES, text)

    # 记录异常到日志
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(erron=RET.DBERR, errmsg='保存图片验证码异常')

    # 返回图片验证码
    else:
        response = make_response(image)
        response.headers['Content-Type'] = 'image/jpg'
        return response

@api.route('/smscode/<mobile>', methods=['GET'])
def send_sms_code(mobile):
    """
    发送短信验证码：获取参数/校验参数/查询数据库/返回结果
    :param mobile:
    :return:
    """
    # 1.获取参数， 图片验证码
    image_code = request.args.get('text')
    image_code_id = request.args.get('id')
    # 2.校验参数的完整性
    if not all([mobile, image_code_id, image_code]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 3.进一步校验参数，手机号
    if not re.match(r'^1[34578]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    # 4.尝试获取真是的图片验证码
    try:
        real_image_code = redis_store.get('ImageCode_'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取图片验证码异常')
    # 5.校验查询结果
    if not real_image_code:
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码过期')
    # 6.比较验证码是否正确
    if  real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')
    # 7.删除缓存中的验证码信息
    try:
        redis_store.delete('ImageCode_'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='缓存清楚失败')
    # 8.验证手机号是否注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询异常')
    # 9.继续校验
    else:
        if user:
            return jsonify(errno=RET.DATAERR, errmsg='该手机号已注册')

    # 10.构造随机验证码
    sms_code = '%06d' % random.randint(1, 999999)
    # 11.首先把验证码存入缓存
    try:
        redis_store.setex('SMSCode_'+mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code )
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存验证码失败')
    # 12.调用云通讯发送短信
    try:
        ccp = sms.CCP()
        # 调用云通讯发短信
        result = ccp.send_template_sms(mobile,[sms_code, constants.SMS_CODE_REDIS_EXPIRES/60], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='短信验证码发送异常')
    # 13. 校验发送结果
    if 0 == result:
        return jsonify(errno=RET.OK, errmsg='ok')
    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送短信失败')



@api.route('/users', methods=['POST'])
def register():
    """
    注册
    :return:
    """
    # 1.获取参数，
    user_data = request.get_json()
    # 2.校验参数是否存在
    if not user_data:
        return jsonify(errno=RET.DATAERR, errmsg='参数错误')
    # 3.进一步获取参数信息
    mobile = user_data.get('mobile')
    sms_code = user_data.get('sms_code')
    password = user_data.get('password')
    # 4.校验参数是否完整
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 5.校验手机号的完整
    if not re.match(r'^1[34578]\d{9}$', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号格式错误')
    # 6.校验短信验证码是否正确
    try:
        real_sms_code = redis_store.get('SMSCode_'+mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取验证码异常')
    # 7.校验查询结果
    if not real_sms_code:
        return jsonify(errno=RET.DATAEXIST, errmsg='短信验证码过期')
    # 8.比较短信验证码
    if real_sms_code != str(sms_code):
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码犯错误')
    # 9.删除缓存
    try:
        redis_store.delete('SMSCode'+mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='缓存清楚失败')
    # 10.校验手机号是否注册
    try:
        user = User.query.filter_by(mobile=mobile).first()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询异常')

    else:
        # 11.校验手机号是否注册
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')
    # 12.存储用户信息，使用模型类存储用户注册信息
    user = User(name=mobile, mobile=mobile)
    # 通过user.password
    user.password = password
    try:
        # 13.调用数据库会话对象保存注册信息，提交数据到mysql数据库
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 14.执行回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存用户信息异常')
    # 15.添加用户信息到缓存中
    session['user_id'] = user.id
    session['name'] = mobile
    session['mobile'] = mobile
    # 16.返回前端相应数据
    return jsonify(errno=RET.OK, errmsg='ok', data=user.to_dict())


# TODO

# 启动
if __name__ == '__main__':
    pass
