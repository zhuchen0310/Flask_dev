# coding=utf-8

"""模型类"""

# 导包
from datetime import datetime
# password加密
from werkzeug.security import generate_password_hash, check_password_hash
# 导入常量包
from ihome import constants
# 导入db
from . import db


# TODO
class BaseModel(object):
    """模型基类，为每个模型添加创建时间和更新时间"""
    create_time = db.Column(db.DATETIME, default=datetime.now)
    update_time = db.Column(db.DATETIME, default=datetime.now, onupdate=datetime.now)


class User(BaseModel, db.Model):
    """用户信息模型类"""
    __tablename__ = 'ih_user_profile'

    id = db.Column(db.Integer, primary_key=True)  # 用户id
    name = db.Column(db.String(32), unique=True, nullable=False)  # 用户名
    password_hash = db.Column(db.String(128), nullable=False)  # 用户密码
    mobile = db.Column(db.String(11), unique=True, nullable=False)  # 手机号
    real_name = db.Column(db.String(32))    # 真名
    id_code = db.Column(db.String(20))    # 身份证号
    avatar_url = db.Column(db.String(128), nullable=False)  # 头像路径
    houses = db.relationship("Hose", backref="user")    # 用户发布的房子
    orders = db.relationship("Order", backref="user")   # 用户下的订单

    # 通过装饰器property, 把password方法提升为属性
    @property
    def password(self):
        """获取password属性时被调用"""
        raise AttributeError("不可读")

    @password.setter
    def password(self, passwd):
        """设置password属性时被调用，将密码加密"""
        self.password_hash = generate_password_hash(passwd)

    def check_password(self, passwd):
        """检查密码正确性"""
        return check_password_hash(self.password_hash, passwd)

    def to_dict(self):
        """将对象转换为字典数据"""
        user_dict = {
            "user_id": self.id,
            "name": self.name,
            "mobile": self.mobile,
            "avatar": constants.QINIU_DOMIN_PREFIX + self.avatar_url if self.avatar_url else "",
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S")

        }
        return user_dict

    def auth_to_dict(self):
        """将实名信息转换为字典"""
        auth_dict = {
            "real_name": self.real_name,
            "user_id": self.id,
            "id_code": self.id_code


        }
        return auth_dict
# 启动
if __name__ == '__main__':
    pass
