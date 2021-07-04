"""
读取插件功能、数据存储配置
除了超管权限特有功能外，其余功能需要通过配置文件进行加载
"""
import yaml
import os

PACKAGE_PATH = 'src.plugins.eve_tools.'
FUNCTION_MAP_PATH = 'src\\plugins\\eve_tools\\utils\\function_map.yaml'

def get_function_map() -> dict:
    func_dict = {}
    with open(FUNCTION_MAP_PATH, 'r', encoding='utf-8') as f:
        func_dict = yaml.load(f, Loader=yaml.SafeLoader)
    return func_dict
