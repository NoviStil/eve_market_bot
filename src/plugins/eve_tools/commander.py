"""
插件主体，提供子方法的调度
“”“
“”“
初始化分为两步：
-加载超管权限功能
    -加载子功能管理相关功能
     加入特殊操作指令
-根据function_map加载扩展子功能
    -加载yaml配置文件
     动态定义响应函数

"""

import importlib

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import Bot, Message, GroupMessageEvent, GROUP_ADMIN, PRIVATE_GROUP, GROUP_OWNER, GROUP

from src.plugins.eve_tools.utils.load_cfg import get_function_map, PACKAGE_PATH
from src.plugins.eve_tools.utils.om import func_mod
from src.plugins.eve_tools.utils.tools import MSG_TYPE_VALUE, MSG_TYPE_KEY_VALUE, MSG_TYPE_ERROR

common_func_map = {}
full_common_func_map: dict = {}
OM_FUNC_MAP = {}
TYPE_REF = {
    'event': Event,
    'group_msg_event': GroupMessageEvent,
    'superuser': SUPERUSER,
    'group_admin': GROUP_ADMIN,
    'group_owner': GROUP_OWNER,
    'group': GROUP,
    'on_command': on_command
}
FUNC_OPERATOR_ON = 'open'
FUNC_OPERATOR_OFF = 'close'
FUNC_RELOAD = 'reload'


def init_mod():
    """初始化公共功能设置"""
    # 加载超管专属功能
    load_om_function()
    # 重新生成方法列表
    reset_functions()


def reset_functions():
    # 清空现有Matcher和绑定的响应方法
    msg = clear_functions()
    func_num = 0
    for item in get_function_map():
        func_num += 1 if load_function(item) else 0
    msg += '加载 [%s] 个功能\n' % func_num
    return msg


def clear_functions():
    """清空所有绑定的响应方法"""
    # 清空common_func_map中绑定的方法
    msg = ''
    func_num = 0
    for name in full_common_func_map:
        func_num += 1 if del_one_function(name) else 0
    # 清空字典
    full_common_func_map.clear()
    common_func_map.clear()
    return '清空 [%s] 个功能\n' % str(func_num)


def load_om_function():
    """加载超管权限功能"""
    svip = on_command('svip', permission=SUPERUSER)

    @svip.handle()
    async def vip_setting(bot: Bot, event: Event, state: T_State):
        inputs = event.get_plaintext()
        cmd = func_mod(inputs)
        cmd_type = cmd.get('type', '')
        if cmd_type == MSG_TYPE_VALUE:
            value = cmd.get('value', '')
            if value == 'func':
                await svip.finish(get_func_list())
            elif value == FUNC_RELOAD:
                await svip.finish(reset_functions())
        elif cmd_type == MSG_TYPE_KEY_VALUE:
            sub_cmd = cmd.get('cmd', '')
            value = cmd.get('value', '')
            if sub_cmd == FUNC_OPERATOR_ON or sub_cmd == FUNC_OPERATOR_OFF:
                msg = func_operator(sub_cmd, value)
                await svip.finish(msg)


def get_func_list():
    """获取已加载的方法列表"""

    msg = ''
    for name, item in full_common_func_map.items():
        func_name = item.get('name', '')
        if func_name:
            msg += func_name
            if func_name in common_func_map:
                msg += ': 已加载\n'
            else:
                msg += ': 未加载\n'
    return msg


def func_operator(ops, func_name):
    """管理方法启用状态"""
    msg = ''
    func_template = {}
    for name, item in full_common_func_map.items():
        if func_name == item.get('name'):
            func_template = item
            break
    else:
        return '未找到扩展功能 [%s]' % func_name

    if ops == FUNC_OPERATOR_ON:
        load_function(func_template)
        msg = '扩展功能 [%s] 已启用' % func_name
    else:
        del_one_function(func_name)
        msg = '扩展功能 [%s] 已停用' % func_name
    return msg


def del_one_function(func_name: str):
    if func_name in common_func_map:
        item = common_func_map.get(func_name)
        item.get('matcher').handlers.clear()
        del common_func_map[func_name]
        return True
    return False


def load_function(item: dict):
    """加载一个功能"""

    # 判断功能基本参数是否丢失
    name = item.get('name', '')
    cmd_type = TYPE_REF.get(item.get('cmd', ''), '')
    func_start = item.get('func_start', '')
    if name and cmd_type and func_start:
        # 删除已有重名功能
        if name in common_func_map:
            del_one_function(name)
        mod = item.get('mod', '')
        func_name = item.get('func')
        eventl = TYPE_REF.get(item.get('event', 'event'), Event)
        permission = item.get('permission', '').split(',')
        pms_modify = item.get('pms_modify', False)
        # 设置权限，自定义时在模块内部自行实现
        if pms_modify or not permission:
            matcher = cmd_type(func_start)
        else:
            sig = True
            for i in permission:
                if sig:
                    perms = TYPE_REF.get(i)
                else:
                    perms = perms | TYPE_REF.get(i)
            matcher = cmd_type(func_start, permission=perms)

        # 定义响应函数
        @matcher.handle()
        async def matcher_func(bot: Bot, event: eventl, state: T_State):
            inputs = event.get_plaintext()
            # 导入依赖包和入口函数
            module = importlib.import_module(PACKAGE_PATH + mod)
            function = getattr(module, func_name)
            msg_reply = function(event, inputs)
            await matcher.finish(msg_reply)

        # 登记方法
        temp = {
            'matcher': matcher,
            'function': matcher_func
        }
        common_func_map[name] = temp
        full_common_func_map[name] = item
        return True
    return False


init_mod()
