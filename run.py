# coding=utf-8
from flask import Flask

def crear_app():
    app = Flask(__name__)
    # 配置信息可以在此处构建
    from app_1_0 import api as api_1_0_buleprint
    app.register_blueprint(api_1_0_buleprint, url_prefix='/api/v1000')
    return app
if __name__ == '__main__':

    app = crear_app()
    app.run(debug=True)