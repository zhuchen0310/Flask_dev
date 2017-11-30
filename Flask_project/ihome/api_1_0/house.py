# -*- coding:utf-8 -*-

"""房屋信息接口"""


# 导包
# 导入api蓝图
from . import api
# 导入flask模块
from flask import session, current_app, jsonify, request
# 导入自定一状态吗
from ihome.utils.response_code import RET
# 导入缓存
from ihome import redis_store, db
# 导入模型
from ihome.models import Area, House, Facility
# 导入json
import json
# 导入常量
from ihome import constants
# 导入登录装饰器
from ihome.utils.commons import login_required
# 检查登录状态
@api.route('/session', methods=['GET'])
def check_login():
    """
    检查登录状态
    :return:
    """
    # 1.通过获取用户缓存信息来检查登录状态
    name = session.get('name')
    # 2.检查用户是否存在
    if name is not None:
        return jsonify(errno=RET.OK, errmsg='ture', data={'name':name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg='false')


@api.route('/arears', methods=['GET'])
def get_area_info():
    """
    获取城区信息
    :return:
    """
    # 1. 尝试从redis中获取缓存城区信息
    try:
        areas = redis_store.get('area_info')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取城区信息失败')
    # 2.校验查询结果
    if areas:
        # 记录访问redis的时间
        current_app.logger.info('hit area info redis')
        # 因为城区信息就是字符串所以直接拼接 不用jsonify
        return '{"errno":0, "errmsg":"ok","data":%s}' % areas
    # 3.缓存没有的话查msq
    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')
    # 4.校验查询结果
    if not areas:
        return jsonify(errno=RET.DBERR, errmsg='查无数据')
    # 5.定义保存数据的列表
    areas_list = []
    for area in areas:
        # 调用Area的to_dict 添加到列表中
        areas_list.append(area.to_dict())
    # 6.把城区信息转换为json格式存入缓存中
    areas_info = json.dumps(areas_list)
    try:
        redis_store.setex('area_info', constants.AREA_INFO_EXPIRES,areas_info)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='缓存存入异常')
    # 7.返回城区信息
    return '{"errno":0, "errmsg":"ok", "data":%s}' % areas_info





@api.route('/houses', methods=['POST'])
@login_required
def save_house_info():
    """
    保存房屋信息
    :return:
    """
    # 1.获取用户id
    user_id = g.user_id
    # 2.获取房屋基本信息
    house_data = request.get_json()
    # 3.校验参数
    if not house_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 4.进一步校验房屋详情信息
    title = house_data.get('title')
    price = house_data.get('price')
    area_id = house_data.get('area_id')
    address = house_data.get('address')
    room_count = house_data.get('room_count')
    acreage = house_data.get('acreage')
    unit = house_data.get('unit')
    capacity = house_data.get('capacity')
    beds = house_data.get('beds')
    deposit = house_data.get('deposit')
    min_days = house_data.get('min_days')
    max_days = house_data.get('max_days')

    # 5.校验参数完成性
    if not all([
        title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit,
        min_days, max_days
    ]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 6.处理价格信息
    try:
        # 由于数据库已分为单位
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='价格转化异常')
    # 7.保存数据到数据库中
    house = House()
    house.user_id = user_id
    house.area_id = area_id
    house.title = title
    house.price = price
    house.addrass = address
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days
    # 8.获取房屋基础设施信息
    facility = house_data.get('facility')
    # 9.校验参数
    if facility:
        try:
            # 过滤掉无效信息
            facilities = Facility.query.filter(Facility.id.in_(facility)).all()
            house.facilities = facilities
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')
    # 10.保存数据
    try:
        db.session.add(house)
        db.session.commit()

    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库添加异常')
    # 11.返回数据
    return jsonify(errno=RET.OK, errmsg='ok', data={"house_id":house.id})

# TODO

# 启动
if __name__ == '__main__':
    pass