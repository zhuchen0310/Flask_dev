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
from flask import current_app, jsonify, make_response
# 导入自定义状态码
from ihome.utils.response_code import RET



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
    1/获取参数，
    :param mobile:
    :return:
    """
# TODO

# 启动
if __name__ == '__main__':
    pass
