"""
将静态数据写入数据库
"""
import yaml
import pymongo
import os
import datetime
import functools
import time
import logging
from src.plugins.eve_tools.utils.tools import SDE_HOME

mg_client = pymongo.MongoClient('mongodb://localhost:27017')
common_db = mg_client['EvePlugins']


# logger = logging.getLogger('load_static')
#
#
# def init_logger():
#     """初始化日志"""
#     logger.setLevel(logging.INFO)
#     sh = logging.StreamHandler()
#     fmt = logging.Formatter(fmt="%(asctime)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s")
#     sh.setFormatter(fmt)
#     logger.addHandler(sh)


def time_cost(func):
    """统计每个文件加载多长时间"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        args[2].info('[%s]解析开始' % args[1])
        msg = func(*args, **kwargs)
        msg['time'] = ': 耗时 %f 秒' % round(time.time() - start, 2)
        args[2].info(msg['message'])
        args[2].info('[%s]解析结束，共耗时[%s]' % (args[1], msg['time']))
        return msg

    return wrapper


def refresh_data(logger: logging, reparse=False):
    # 初始化日志
    # init_logger()

    if reparse:
        # 加载yaml
        logger.info('开始解析静态数据')
        blueprint = os.path.join(SDE_HOME, 'blueprints.yaml')
        category = os.path.join(SDE_HOME, 'categoryIDs.yaml')
        group = os.path.join(SDE_HOME, 'groupIDs.yaml')
        dogma_attr = os.path.join(SDE_HOME, 'dogmaAttributes.yaml')
        type_dogma = os.path.join(SDE_HOME, 'typeDogma.yaml')
        type_id = os.path.join(SDE_HOME, 'typeIDs.yaml')
        attr_category = os.path.join(SDE_HOME, 'dogmaAttributeCategories.yaml')
        icon = os.path.join(SDE_HOME, 'iconIDs.yaml')
        msg_list = list()
        # msg_list.append(load_yaml(blueprint, 'blueprint', logger))
        # msg_list.append(load_yaml(category, 'categoryID', logger))
        # msg_list.append(load_yaml(group, 'groupID', logger))
        # msg_list.append(load_yaml(dogma_attr, 'dogmaAttr', logger))
        # msg_list.append(load_yaml(type_dogma, 'typeDogma', logger))
        # msg_list.append(load_yaml(type_id, 'typeID', logger))
        # msg_list.append(load_yaml(attr_category, 'dogmaAttrCategory', logger))
        # icon需要单独解析处理
        msg_list.append(parse_icon(icon, 'iconIDs', logger))
    return msg_list


# 生成中间、缓存表
def generate_cache(logger: logging):
    pass


# 生成中间、缓存表结束

# 属性解析
def parse_attr(item_id: int, logger: logging) -> dict:
    item_st = common_db['typeID']
    dogma_st = common_db['typeDogma']
    group_st = common_db['groupID']
    dgm_attr_st = common_db['dogmaAttr']
    dgm_category_st = common_db['dogmaAttrCategory']
    category_st = common_db['categoryID']
    if isinstance(item_id, str) and item_id.isdigit():
        item_id = int(item_id)
    if not isinstance(item_id, int):
        logger.warning('属性解析: 输入id[%s]不合法' % item_id)
        return False
    item = item_st.find_one({'_id': item_id})
    dogma = dogma_st.find_one({'_id': item_id})
    if item is not None:
        item_new = item
        # 查询所属group
        group_id = item.get('groupID')
        if group_id:
            # 只保留groupid和名称(优先中文)
            group_item = group_st.find_one({'_id': int(group_id)})
            del item_new['groupID']
            if group_item:
                # 解析groupID
                group_item_new = dict()
                group_item_new['_id'] = int(group_id)
                category_id = group_item.get('categoryID')
                group_name = group_item.get('name')
                if group_name:
                    name = group_name.get('zh') if group_name.get('zh', '') else group_name.get('en')
                    group_item_new['name'] = name
                item_new['group'] = group_item_new

                # 解析categoryID
                if category_id:
                    category_item = category_st.find_one({'_id': category_id})
                    if category_item:
                        category_item_new = dict()
                        category_item_new['_id'] = category_id
                        category_name = category_item.get('name')
                        if category_name:
                            name = category_name.get('zh') if category_name.get('zh') else category_name.get('en')
                            category_item_new['name'] = name
                        item_new['category'] = category_item_new
    else:
        logger.warning('属性解析: id[%d]不存在' % item_id)
        return False
    # 解析typeDogma
    if dogma:
        item_new['attrs'] = dict()
        dgm_list = dogma.get('dogmaAttributes')
        item_attr = dict()
        for dgm in dgm_list:
            attr_id = dgm.get('attributeID')
            value = dgm.get('value')
            data_type = dgm.get('dataType')
            # 获取属性对应类别
            dgm_attr = dgm_attr_st.find_one({'_id': attr_id})
            if dgm_attr:
                attr_name = dgm_attr.get('name')    # 充当标签
                attr_cate_id = dgm_attr.get('categoryID')
                if attr_cate_id:
                    attr_cate = dgm_category_st.find_one({'_id': attr_cate_id})
                    if attr_cate:
                        root_key = attr_cate.get('name')
                        temp = item_new['attrs'].get(root_key)
                        attr_dct = {'value': value,
                                    'dataType': data_type}
                        if temp:
                            temp[attr_name] = attr_dct
                        else:
                            item_new['attrs'][root_key] = dict()
                            item_new['attrs'][root_key][attr_name] = attr_dct
    return item_new

# 属性解析结束

# 加载yaml
@time_cost
def load_yaml(path, sheet: str, logger: logging, database: str = 'EvePlugins') -> dict:
    """
    将指定yaml写入到对应数据库特定的表中
    :param path: yaml文件路径
    :param sheet: 数据表名称
    :param database: 数据库名称
    :return: 写入反馈信息
    {
        'state': True/False,
        'message': ''
    }

    注意：yaml中的根节点对应物品/属性id，
        由于后续会用到大量反向查询，所以必须将其转换为_id属性的值来保存，
        否则查询难度极大
    """
    file_name = os.path.basename(path)
    msg = {}
    upd_sheet = sheet + '_upd'  # 更新数据库
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            # 此处只能用BaseLoader，否则对于int类型的key插入数据库会报错
            data = yaml.load(f, Loader=yaml.BaseLoader)
            # 加载数据库
            db = mg_client[database]
            detail = db[sheet]
            detail_upd = db[upd_sheet]
            # 若加入更新比对，在此处进行更改
            data_ori = []  # 存放已有的id
            for item in detail.find():
                data_ori.append(item.get('_id'))

            data_list, data_new = get_upgrade_data(data, data_ori)
            # 清空数据库，并重新写入
            detail.delete_many({})
            detail.insert_many(data_list)
            if len(data_new) > 0:
                detail_upd.insert_many(data_new)

            count_new = len(data_new)
            msg['state'] = True
            msg['message'] = '成功更新 [%s] ， 新增 [%s] 条数据' % (file_name, str(count_new))
    else:
        msg['state'] = False
        msg['message'] = '未找到文件 [%s]' % file_name

    return msg


@time_cost
def parse_icon(path, sheet: str, logger: logging, database: str = 'EvePlugins') -> dict:
    file_name = os.path.basename(path)
    msg = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            # 此处只能用BaseLoader，否则对于int类型的key插入数据库会报错
            data = yaml.load(f, Loader=yaml.BaseLoader)
            # 加载数据库
            db = mg_client[database]
            detail = db[sheet]
            # 清空数据库，并重新写入
            detail.delete_many({})
            update_list = list()
            for key, value in data.items():
                item = dict()
                item['_id'] = int(key)
                f_path = value.get('iconFile').split('/')
                if f_path[-2] == 'icons' or f_path[-2] == 'corps':
                    icon_path = os.path.join(f_path[-2], f_path[-1])
                    item['src'] = icon_path
                    update_list.append(item)

            detail.insert_many(update_list)
            msg['state'] = True
            msg['message'] = '成功更新 [%s] ， 新增 [%s] 条数据' % (file_name, str(len(update_list)))
    else:
        msg['state'] = False
        msg['message'] = '未找到文件 [%s]' % file_name

    return msg


def get_upgrade_data(data: dict, origin: list):
    """
    根据新数据和已有id，生成更新项目
    :param data:
    :param origin:
    :return:

    """
    data_list = []
    data_new = []
    date = datetime.date.today()
    for i in data:
        # 转换data格式
        temp = dict()
        temp['_id'] = int(i)
        for attr in data[i]:
            if 'masteries' == attr:
                continue
            temp[attr] = data[i][attr]
        data_list.append(temp)
        # 如果有新增id，则记录下它
        if temp['_id'] not in origin:
            # 新增更新时间
            temp_new = temp
            temp_new['upd_date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            data_new.append(temp_new)
    return data_list, data_new
# 加载yaml结束

