# -*- coding:utf-8 -*-

"""订单模块"""


# 导包
# 导入蓝图
from . import api
# 导入验证登录器
from ihome.utils.commons import login_required
# flask
from flask import request, jsonify, current_app, g
# 导入自定义状态码
from ihome.utils.response_code import RET
# 导入时间模块
import datetime
# 导入模型类
from ihome.models import User, House, Order
# 导入db
from ihome import db
# 导入缓存
from ihome import redis_store


@api.route('/orders', methods=['POST'])
@login_required
def save_order():
    """
    保存订单
    :return:
    """
    # 获取用户id
    user_id = g.user_id
    # 获取参数，校验参数
    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 进一步获取详细参数信息
    house_id = order_data.get('house_id')
    start_date_str = order_data.get('start_date')
    end_date_str = order_data.get('order_date')
    # 检验参数完整性
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 对日期格式化处理
    try:
        start_date = datetime.datetime.strptime(start_date_str)
        end_date = datetime.datetime.strptime(end_date_str)
        # 断言开始时间小于结束时间
        assert start_date <= end_date
        # 计算预定天数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期格式错误')
    # 查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取房屋信息失败')
    # 校验查询结果
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')
    # 判断是否为房东
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg='不能预定自己的订单')
    # 查询时间冲突的订单数
    try:
        count = Order.query.filter(Order.house_id == house_id,
                                   Order.begin_date <= end_date,
                                   Order.end_date >= start_date
                                   ).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')
    # 校验查询结果
    if count > 0 :
        return jsonify(errno=RET.DATAERR, errmsg='房屋已被预定')
    # 计算房屋总价
    amount = days * house.price
    # 生成模型类对象， 保存订单基本信息：房屋/用户/订单开始日期/订单结束日期/天数/x
    order = Order()
    order.house_id = house_id
    order.user_id = user_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = amount
    # 保存订单数据到数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存订单失败')
    # 前端对应服务器的操作如果是更新资源或新建资源，可以返回结果
    return jsonify(errno=RET.OK, errmsg='ok', data={'order_id':order.id})


@api.route('/user/orders', methods=['GET'])
@login_required
def get_user_orders():
    """
    查询用户的订单信息
    :return:
    """
    user_id = g.user_id

    # 用户的身份， 用户想要查询作为房客预定别人房子的订单，还是作为房东想查询别人预定的订单
    role = request.args.get('role', '')
    # 查询订单数据
    try:
        # 如果是房东角色
        if 'landlord' == role:
            # 以房东的身份查询订单
            houses = House.query.filter(House.user_id == user_id).all()
            house_ids = [house.id for house in houses]
            # 再查询预定自己房子的订单，默认按照房屋订单发布的时间进行倒叙排序
            orders = Order.query.filter(Order.house_id.in_(house_ids)).order_by(Order.create_time.desc()).all()
        else:
            # 以房客的身份查询订单，查询直接预定的订单
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')
    # 将订单对象转换为字典数据
    order_dict_list = []
    # 校验查询结果
    if orders:
        for order in orders:
            order_dict_list.append(order.to_dict())
    return jsonify(errno=RET.OK, errmsg='ok', data={'orders':order_dict_list})


@api.route('/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def accept_reject_order(order_id):
    """
    接单， 拒单
    :param order_id:
    :return:
    """
    # 获取用户信息
    user_id = g.user_id
    # 获取参数信息，校验参数存在
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # action 参数表明客户端请求的是接单还是拒单行为
    action = req_data.get('action')
    if action not in ('accept', 'reject'):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id == order_id, Order.status == 'WAIT_ACCEPT').first()
        # 查询所有房屋
        house = Order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单信息')

    # 确保房东只能修改属于自己房子的订单
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg='操作无效')
    # 如果房东选择接单操作
    if action == 'action':
        # 接单， 将订单状态设置为等待评论
        order.status = 'WAIT_COMMENT'
    # 如果房东选择拒单
    elif action == 'reject':
        # 拒单，要求用户传递拒单原因
        reason = req_data.get('reason')
        # 判断房东是否填写拒单原因
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        # 如果房东选择拒单，把拒单原因保存到数据库
        order.status = 'REJECTED'
        # comment字段保存拒单原因
        order.comment = reason
    # 把接单或拒单存储到数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')
    return jsonify(errno=RET.OK, errmsg='ok')


@api.route('/orders/<int:order_id>/comment', methods=['PUT'])
@login_required
def save_order_comment(order_id):
    """
    保存订单评论信息
    :param order_id:
    :return:
    """
    # 获取用户信息
    user_id = g.user_id
    # 获取参数
    req_data = request.get_json()
    # 尝试获取评论内容
    comment = req_data.get('comment')
    # 要求用户必须填写评论内容
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='还没有评论')
    # 查询订单数据
    try:
        # 根据订单id/订单所属用户/订单状态
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status
                                   == 'WAIT_COMMENT').first()
        # 查询订单所属房屋
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单信息')
    # 校验查询结果
    if not order:
        return jsonify(errno=RET.REQERR, errmsg='操作无效')
    # 保存评价信息
    try:
        # 将订单的状态设置为已完成
        order.status = 'COMPLETE'
        # 保存订单评价信息
        order.comment = comment
        # 将房屋的完成订单数量+1， 如果订单已评价，让房屋成交量+1
        house.order_count += 1
        # add_all 提交 修改的数控
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')
    # 缓存中的房屋信息，因为订单成交，导致缓存中的数据已经过期，需要删除过期数据
    try:
        redis_store.delete('house_info_%s' % order.house.id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='添加缓存异常')
    # 最终返回状态码
    return jsonify(errno=RET.OK, errmsg='ok')
# TODO

# 启动
if __name__ == '__main__':
    pass