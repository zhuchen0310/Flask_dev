# coding=utf-8

"""常量信息，数据库缓存，验证码，房屋信息等"""

# 导包

# 图片验证码redis的有效时间, 单位：秒
TMAGE_CODE_REDIS_EXPIRES = 300

# 短信验证码缓存有效时间， 单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 七牛空间域名 # todo 使用自己的域名
QINIU_DOMIN_PREFIX = "http://***********.bkt.clouddn.com/"

# 城区信息缓存时间，单位：秒
AREA_INFO_EXPIRES = 7200

# 首页展示房屋数量：5
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据缓存存放时间，单位：秒
HOME_PAGE_DATA_REDIS_EXPRIES = 7200

# 房屋详情页展示的最大评论数：30
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋详情页面缓存存放时间，单位：秒
HOUSE_DETAIL_REDIS_EXPRIES_SECOND = 7200

# 房屋列表页每页展示房屋数量：2
HOUSE_LIST_PAGE_CAPACITY = 2

# 房屋列表页面缓存有效时间，单位：秒
HOUSE_LIST_REDIS_EXPIRES = 7200

# TODO

# 启动
if __name__ == '__main__':
    pass