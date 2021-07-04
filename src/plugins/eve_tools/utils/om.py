"""
实现超管权限
"""
from src.plugins.eve_tools.utils.tools import MSG_TYPE_KEY_VALUE, \
    MSG_TYPE_VALUE, MSG_TYPE_ERROR, INVALID_INPUT_TYPE, TOO_MANY_ARGS, MSG_TYPE_BASE


def func_mod(inputs: str) -> dict:
    """切分输入参数，转换成值、子命令+值的格式"""
    """
    :return msg:
    {
        'type':         类型，必选
        'cmd':          子命令，可选
        'value':        值，可选
        'multiplier':   倍数，可选
    }
    """
    msg = {}
    if not isinstance(inputs, str):
        msg['type'] = MSG_TYPE_ERROR
        msg['value'] = INVALID_INPUT_TYPE
    else:
        str_list = inputs.split(' ')
        if len(str_list) > 2:
            msg['type'] = MSG_TYPE_ERROR
            msg['value'] = TOO_MANY_ARGS
        else:
            arg1 = str_list[0]
            arg1_list = arg1.split('*')
            if len(arg1_list) == 2:
                msg['multiplier'] = arg1_list[1]
            if len(str_list) == 2:
                msg['type'] = MSG_TYPE_KEY_VALUE
                msg['cmd'] = arg1_list[0]
                msg['value'] = str_list[1]
            elif len(arg1_list) == 1:
                msg['type'] = MSG_TYPE_VALUE
                msg['value'] = arg1_list[0]
            else:
                msg['type'] = MSG_TYPE_BASE
    return msg
