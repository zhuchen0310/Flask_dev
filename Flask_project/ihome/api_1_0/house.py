# -*- coding:utf-8 -*-

"""房屋信息接口"""

# 导包
# 导入api蓝图
from . import api
# 导入flask模块
from flask import session, current_app, jsonify, request, g
# 导入自定一状态吗
from ihome.utils.response_code import RET
# 导入缓存
from ihome import redis_store, db
# 导入模型
from ihome.models import Area, House, Facility, HouseImage, User
# 导入json
import json
# 导入常量
from ihome import constants
# 导入登录装饰器
from ihome.utils.commons import login_required
# 导入七牛云存储
from ihome.utils.image_storage import storage


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
        return jsonify(errno=RET.OK, errmsg='ture', data={'name': name})
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
        redis_store.setex('area_info', constants.AREA_INFO_EXPIRES, areas_info)

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
    return jsonify(errno=RET.OK, errmsg='ok', data={"house_id": house.id})


@api.route('/houses/<int:house_id>/images', methods=['POST'])
@login_required
def save_house_image(house_id):
    """
        保存房屋图片
        1/获取参数，house_image
        2/校验参数存在
        3/校验房屋是否存在,读取图片数据，调用七牛云接口上传图片
        4/构造模型类对象，保存房屋图片数据
        5/判断房屋主图片是否设置，如未设置保存当前图片为房屋主图片
        6/保存数据到数据库中
        7/拼接完整的图片url返回前端
        :param house_id:
        :return:
        """
    # 1. 获取参数
    house_image = request.files.get('house_image')
    # 2.校验参数存在
    if not house_image:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 3.校验房屋是否存在
    try:
        house = House.query.get('house_id')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='房屋查询异常')
    # 4.房屋不存在
    if not house:
        return jsonify(errno=RET.PARAMERR, errmsg='房屋不存在')
    # 5.读取图片数据
    house_image_data = house_image.read()
    # 6.保存到七牛云
    try:
        house_image_name = storage(house_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片异常')
    # 7.构造模型类对象，保存房屋图片数据
    house_images = HouseImage()
    house_images.house_id = house_id
    house_images.url = house_image_name
    # 8.保存数据到数据库中
    db.session.add(house_images)
    # 9.判断房屋主图片是否设置
    if not house.index_image_url:
        house.index_image_url = house_image_name
        db.session.add(house)
    # 10.保存房屋图片到数据库中
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库保存房屋图片异常')
    # 11.保存房屋图片到缓存中
    try:
        redis_store.setex('House_image' + house_id, constants.HOME_PAGE_DATA_REDIS_EXPRIES, house_image_name)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='缓存图片异常')
    # 12.拼接图片完整url 返回前端
    image_url = constants.QINIU_DOMIN_PREFIX + house_image_name
    return jsonify(errno=RET.OK, errmsg='ok', data={"url": image_url})


@api.route('/house/index', methods=['GET'])
def get_house_index():
    """
       项目首页幻灯片信息展示
       1/尝试从redis中获取房屋信息
       2/校验获取结果
       3/查询mysql数据库,默认把成交量最高的五套房屋数据返回
       4/校验查询结果
       5/定义列表存储多条数据,判断房屋是否设置主图片信息,如未设置,默认不添加数据
       6/把数据存入缓存中
       7/返回前端最终的查询结果
       :return:
       """
    # 1. 从缓存获取数据
    try:
        ret = redis_store.get('home_page_data')
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    # 2. 校验获取结果
    if ret:
        current_app.logger.info(" hide redis get house_index")
        return '{"errno":0, "errmsge":"ok", "data":%s}' % ret

    # 3.查询mysql数据看
    try:
        house_info = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库异常')
    # 4.校验查询结果
    if not house_info:
        return jsonify(errno=RET.DATAERR, errmsg='查询无结果')
    # 5.定义列表存储多条数据,判断房屋是否设置主图片信息,如未设置,默认不添加数据
    houses = []
    for house in house_info:
        if not house.index_image_url:
            continue
        houses.append(house.to_basic_dict())
    # 6.json话数据
    json_houses = json.dumps(houses)
    # 7.存入缓存中
    try:
        redis_store.setex('home_page_data', constants.HOME_PAGE_DATA_REDIS_EXPRIES, json_houses)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='缓存首页失败')
    # 8.返回数据
    ret_json = json_houses
    return '{"errno":0, "errmsg":"ok", "data":%s}' % ret_json


@api.route('/houses/<int:house_id>', methods=['GET'])
def get_house_detail(house_id):
    """
    获取房屋详情信息
    1/获取用户信息,用来校验用户身份
    2/获取house_id,校验参数
    3/尝试从缓存中查询房屋详情信息
    4/校验查询结果
    5/如未获取数据,查询mysql数据库
    6/转换数据格式,调用模型类中的to_full_dict()方法
    7/序列化数据,把数据存入缓存中
    8/返回结果
    :param house_id:
    :return:
    """
    # 1.获取用户信息,-1代表是房东
    user_id = session.get('user_id', "-1")
    # 2.检验用户house_id
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 3.尝试从缓存中查询房屋信息
    try:
        house_detail = redis_store.get('house_info_%s') % house_id
    except Exception as e:
        current_app.logger.error(e)
        house_detail = None
    # 4.校验参数结果
    if house_detail:
        current_app.logger.info('hide redis get house_detail')
        return "{'errno':0, 'errmsg':'ok', 'data':{'user_id':%s, 'house':%s}}" % (user_id, house_detail)
    # 5.查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询房屋信息异常')
    # 6.校验参数
    if not house:
        return jsonify(errno=RET.DATAERR, errmsg='无房屋数据')
    # 7.获取房屋详情
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='房屋信息格式错误')
    # 8.序列化  保存到缓存
    json_house = json.dumps(house_data)
    try:
        redis_store.setex('house_info_%s' % house_id, constants.HOUSE_DETAIL_REDIS_EXPRIES_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    # 9.构造响应数据
    resp = '{"errno":0, "errmsg":"ok","data":{"user_id":%s, "house":%s}}' % (user_id, json_house)
    return resp


@api.route('/user/houses', methods=['GET'])
@login_required
def get_user_houses():
    """
    获取用户房屋信息
    :return:
    """
    # 1.获取参数user_id
    user_id = g.user_id
    # 2.查询数据库
    try:
        user = User.query.get(user_id)
        # 3.使用反向引用查询用户的房屋
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询房屋信息失败')
    # 4.校验查询结果
    if not houses:
        return jsonify(errno=RET.NODATA, errmsg='没有房屋')
    # 5.存储查询结果
    houses_list = []
    for house in houses:
        houses_list.append(house.to_basic_dict())
    # 6.返回结果
    return jsonify(errno=RET.OK, errmsg='ok', data={"houses": houses_list})


# TODO

# 启动
if __name__ == '__main__':
    pass
