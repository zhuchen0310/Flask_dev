# coding=utf-8

"""七牛云存储业务逻辑"""

# 导包
import logging

from qiniu import Auth, put_data

# 需要填写自己的 Access Key 和 Secret Key

access_key = 'Sy3B5eX9iv-RFMbXUbbZTPQdxMN4IJdXLNODGeYI'
secret_key = 'J4Imd0sZ2go-WZguEGOsKD4TtcwsQJu5ngJYkanl'

# 要上传的空间名称
bucket_name = 'ihome'

def storage(data):
    """七牛云存储上传文件接口"""
    if not data:
        return None
    try:
        # 构建鉴权对象
        q = Auth(access_key, secret_key)
        #
        # 上传到七牛后保存的文件名
        # key = 'my-python-logo.png';
        # 生成上传 Token，可以指定过期时间等
        # token = q.upload_token(bucket_name, key, 3600)
        #
        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(bucket_name)
        #
        # 要上传文件的本地路径
        # localfile = './sync/bbb.jpg'
        # ret, info = put_file(token, key, localfile)
        ret, info = put_data(token, None, data)

    except Exception as e:
        logging.error(e)
        raise e

    if info and info.status_code != 200:
        raise Exception("上传文件失败")

    # 返回上传的文件名
    # print ret["key"]
    return ret["key"]


# 启动
if __name__ == '__main__':
    file_name = raw_input("请输入文件名")
    with open(file_name, "rb") as f:
        storage(f.read())
