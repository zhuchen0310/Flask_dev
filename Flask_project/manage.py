# -*- coding:utf-8 -*-

"""项目启动文件"""

# 导包
from ihome import create_app, db

from flask_script import Manager

from flask_migrate import Migrate, MigrateCommand

# 实例化app 已开发者模式
app = create_app("development")

# 创建数据表
Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


# TODO

# 启动
if __name__ == '__main__':
    print app.url_map
    manager.run()