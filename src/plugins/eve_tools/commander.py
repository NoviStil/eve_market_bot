import importlib

from nonebot import on_command
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import Bot, Message, GroupMessageEvent, GROUP_ADMIN, PRIVATE_GROUP, GROUP_OWNER, GROUP

from src.plugins.eve_tools.utils.load_cfg import get_function_map, PACKAGE_PATH

COMMON_FUNC_MAP = {}
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
cfg = on_command('cfg')
test_cfg = on_command('test')
func_map = {'func': test_cfg}


def init_mod():
    """初始化公共功能设置"""
    common = get_function_map()
    for item in common:
        load_function(item)


def load_function(item: dict):
    """加载一个功能"""

    # 判断功能基本参数是否丢失
    name = item.get('name', '')
    cmd_type = TYPE_REF.get(item.get('cmd', ''), '')
    func_start = item.get('func_start', '')
    if name and cmd_type and func_start:
        # 删除已有重名功能
        if name in COMMON_FUNC_MAP:
            del COMMON_FUNC_MAP[name]
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
        COMMON_FUNC_MAP['name'] = temp


@cfg.handle()
async def cmd_config(bot: Bot, event: GroupMessageEvent, state: T_State):
    inputs = event.get_plaintext()
    print(inputs)
    await cfg.finish(inputs)


@func_map['func'].handle()
async def new_func(bot: Bot, event: GroupMessageEvent, state: T_State):
    inputs = event.get_plaintext()
    inputs += ' this is a test'
    print(inputs)
    await func_map['func'].finish(inputs)


init_mod()
