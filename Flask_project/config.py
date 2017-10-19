# coding=utf-8

# 导包
import redis


# 类
class Config:
    """
    基本配置类
    """
    # token
    SECRET_KEY = 'TQ343dfsdf34+SDjjojlje343ET+?#$ODFDSFSD'

    # flask_SQLALchemy配置
    #
    # mysql配置
    SQLALCHEMY_DATABASE_URI = 'mysql://python:python123456@127.0.0.1/ihome8'
    #
    # 追踪数据库的修改行为
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 创建 redis参数
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # flask-session 使用参数
    SESSION_TYPE = "redis"  # 利用redis 来保存session会话
    #
    SESSION_USE_SIGNER = True  # 为sesson_id进行签名
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # redis 缓存设置
    #
    PERMANENT_SESSION_LIFETIME = 86400  # session数据的有效期 秒


class DevelopmentConfig(Config):
    """
    开发模式的参数配置
    """
    DEBUG = True


class ProductionConfig(Config):
    """
    生产环境配置
    """
    pass


# 配置参数选择
config = {
    "development": DevelopmentConfig,  # 开发者模式
    "production": ProductionConfig,  # 生产环境
}


