"""存放通用方法"""

import requests
import os

################### 返回消息格式

MSG_TYPE_KEY_VALUE = 'key-value'
MSG_TYPE_VALUE = 'value'
MSG_TYPE_IMAGE = 'image'
MSG_TYPE_ERROR = 'error'
MSG_TYPE_BASE = 'base'

################### 错误类型
INVALID_INPUT_TYPE = '输入类型错误'
TOO_MANY_ARGS = '参数过多参数'

SDE_URL = 'https://eve-static-data-export.s3-eu-west-1.amazonaws.com/tranquility/sde.zip'
IMG_URL = 'https://images.evetech.net/types/%s/render?size=%s&tenant=singularity'
SDE_HOME = 'src\\plugins\\eve_tools\\static_data'


# def get_sde():
#     zip_path = os.path.join(SDE_HOME, 'sde.zip')
#     sde_dir = os.path.join(SDE_HOME, 'sde')
#     # 如果压缩包存在则删除
#     if os.path.exists(zip_path):
#         os.remove(zip_path)
#     resp = requests.get(SDE_URL)
