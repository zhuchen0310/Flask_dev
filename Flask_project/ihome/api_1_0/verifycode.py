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
from flask import current_app, jsonify, make_response, request
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

@api.route('/smscode/<mobile>', method=['GET'])
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
    # 3.

# TODO

# 启动
if __name__ == '__main__':
    pass
