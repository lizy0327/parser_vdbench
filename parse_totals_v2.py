#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
File       : parse_totals_v2.py
Time       : 2023-06-20 14:44
Author     : lizy
Email      : lizy0327@gmail.com
Version    : python 3.9
Software   : PyCharm
Description: VDBench 性能分析工具 v2 - 优化重构版
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import time
from binascii import a2b_hex
from typing import Dict, List, Optional, Tuple

import pandas as pd
from Cryptodome.Cipher import AES

# 时间格式正则匹配 HH:MM:SS.SSS
TIME_PATTERN = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3}$')


def is_time_format(line: str) -> bool:
    """检查字符串是否为 HH:MM:SS.SSS 时间格式"""
    if len(line) < 12:
        return False
    return bool(TIME_PATTERN.match(line[:12]))


def parse_file_totals(html_path: str) -> Tuple[List[List[str]], List[List[str]]]:
    """
    解析 vdbench 生成的 file 类型的 totals.html 文件

    :param html_path: HTML 文件路径
    :return: (title_lists, data_lists)
    """
    try:
        title_lists = []
        data_lists = []

        with open(html_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()

                # 过滤 RD=format 这种埋数据的数据，处理标题内容
                if "RD=format" not in line and "name" in line and "<a" in line:
                    start_tag = '<b>'
                    end_tag = '</b>'
                    start_index = line.find(start_tag) + len(start_tag)
                    end_index = line.find(end_tag)

                    if start_index != -1 and end_index != -1:
                        data = line[start_index:end_index]
                        # 去除;和.
                        data1 = data.replace(";", "")
                        # 去除不需要的字段
                        title_list = data1.split()
                        # 安全移除不需要的字段
                        remove_keywords = ["Starting", "For", "loops:", "None"]
                        title_list = [item for item in title_list if item not in remove_keywords]
                        title_lists.append(title_list)

                # 处理性能数据，过滤掉埋数据以及检查文件的 rd 结果
                # 第 20 个元素描述的是 create 的性能，第 3 个元素是真正的性能值
                if "avg" in line and is_time_format(line):
                    parts = line.split()
                    if len(parts) > 19 and parts[19] == '0.0' and parts[2] != '0.0':
                        data_list = [item for item in parts if "avg" not in item]
                        data_lists.append(data_list)

        return title_lists, data_lists

    except SyntaxError:
        print(f"the file: {html_path} is not html format")
        raise
    except Exception as file_e:
        print(f"Error parsing file totals: {file_e}")
        raise


def file_list_to_dict(title_lists: List[List[str]], data_lists: List[List[str]],
                      is_debug: bool = False) -> Dict[str, List]:
    """
    把多条 list 数据提取相同的数据类型分别写入不同的 list，并写入字典

    :param title_lists: 标题列表
    :param data_lists: 数据列表
    :param is_debug: 是否打印调试信息
    :return: 性能数据字典
    """
    data_dict = {}

    # 如果第 1 个 list 的总数大于第 2 个 list，说明有未完成的 rd，需要删除
    if len(title_lists) - len(data_lists) == 1:
        title_lists.pop()

    # 处理 title list 数据
    start_time_list = [item[0] for item in data_lists]
    # 删除每个子列表的第一个时间元素，将每个子列表转换为字典
    temp_list1 = [sublist[1:] for sublist in title_lists]
    title_dict_result = [dict(item.split('=') for item in sublist) for sublist in temp_list1]

    # 对于某些不是必须的参数，需要判断是否存在
    data_dict.update({
        'start time': start_time_list,
        'rd name': [item.get('RD') for item in title_dict_result],
        'elapsed': [int(item.get('elapsed')) if item.get('elapsed') else None for item in title_dict_result],
        'warmup': [int(item.get('warmup')) if item.get('warmup') else None for item in title_dict_result],
        'rate': [item.get('fwdrate', '').replace(".", "") for item in title_dict_result],
        'rdpct': [int(item.get('rdpct')) if item.get('rdpct') else None for item in title_dict_result],
        'xfersize': [item.get('xfersize') for item in title_dict_result],
        'threads': [item.get('threads') for item in title_dict_result],
    })

    # 处理 data list 数据，把所有数字转换为 float
    columns_to_convert = [1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    column_names = ['iops', 'resp', 'read pct', 'read rate', 'read resp', 'write rate', 'write resp',
                    'read mbps', 'write mbps', 'total mbps', 'xfer size']

    for name, index in zip(column_names, columns_to_convert):
        data_dict[name] = [float(item[index]) for item in data_lists]

    if is_debug:
        print(data_dict)

    return data_dict


def parse_block_totals(html_path: str) -> Tuple[List[List[str]], List[List[str]]]:
    """
    解析 vdbench 生成 block 的 totals.html 文件

    :param html_path: HTML 文件路径
    :return: (title_lists, data_lists)
    """
    try:
        title_lists = []
        data_lists = []

        with open(html_path, 'r', encoding='utf-8') as block_file:
            for line in block_file:
                line = line.strip()

                # 处理标题内容
                if "name" in line and "<a" in line:
                    start_tag = '<b>'
                    end_tag = '</b>'
                    start_index = line.find(start_tag) + len(start_tag)
                    end_index = line.find(end_tag)

                    if start_index != -1 and end_index != -1:
                        data = line[start_index:end_index]
                        data1 = data.replace(";", "")
                        title_list = data1.split()

                        # 安全移除不需要的字段
                        remove_keywords = ["Starting", "For", "loops:", "I/O", "None",
                                          "Uncontrolled", "Controlled"]
                        title_list = [item for item in title_list if item not in remove_keywords]
                        title_lists.append(title_list)

                # 处理性能数据
                if is_time_format(line):
                    data_list = line.split()
                    data_lists.append(data_list)

        # 处理时间和 avg 连在一起的特殊情况
        cleaned_data_lists = []
        for item in data_lists:
            if item and "avg" in item[0]:
                # 时间和 avg 连在一起，分离它们
                item[0] = item[0][:12]
            if len(item) > 1 and "avg" in item[1]:
                # 第 2 列包含 avg 关键字，删除第 2 列
                item = item[:1] + item[2:]
            cleaned_data_lists.append(item)

        return title_lists, cleaned_data_lists

    except SyntaxError:
        print(f"the block file: {html_path} is not html format")
        raise
    except Exception as block_e:
        print(f"Error parsing block totals: {block_e}")
        raise


def block_list_to_dict(title_lists: List[List[str]], data_lists: List[List[str]],
                       is_debug: bool = False) -> Dict[str, List]:
    """
    把多条 list 数据提取相同的数据类型分别写入不同的 list，并写入字典

    :param title_lists: 标题列表
    :param data_lists: 数据列表
    :param is_debug: 是否打印调试信息
    :return: 性能数据字典
    """
    data_dict = {}

    # 如果第 1 个 list 的总数大于第 2 个 list，说明有未完成的 rd，需要删除
    if len(title_lists) - len(data_lists) == 1:
        title_lists.pop()

    # 处理 title list 数据
    start_time_list = [item[0] for item in data_lists]
    rate_list = [item[3] for item in title_lists]

    # 删除第 1 个元素，再删除第 2 个 (rate) 和第 3 个 (rate 的值) 元素
    temp_list1 = [sublist[1:] for sublist in title_lists]
    temp_list2 = [item[:1] + item[3:] for item in temp_list1]

    # 将剩下的 list 转换为字典
    title_dict_result = [dict(item.split('=') for item in sublist) for sublist in temp_list2]

    # 由于 RD 使用的参数不同，会导致 title 内容有差异，以下参数不是必须的
    data_dict.update({
        'start time': start_time_list,
        'rd name': [item.get('RD') for item in title_dict_result],
        'rate': rate_list,
        'elapsed': [int(item.get('elapsed')) if item.get('elapsed') else None for item in title_dict_result],
        'warmup': [int(item.get('warmup')) if item.get('warmup') else None for item in title_dict_result],
        'rdpct': [int(item.get('rdpct')) if item.get('rdpct') else None for item in title_dict_result],
        'xfersize': [item.get('xfersize') for item in title_dict_result],
        'threads': [item.get('threads') for item in title_dict_result],
    })

    # 处理性能数据 - 删除每个子列表的第一个时间元素
    # 原始数据列顺序：['iops', 'mbps', 'bytes', 'read pct', 'resp time', 'read resp', 'write rate',
    #                 'resp max', 'resp stddev', 'queue depth', 'cpu% sys+u', 'cpu% sys']
    # resp time 放在 mbps 后面（索引 4 的数据移到输出列的第 3 位）
    no_time_lists = [sublist[1:] for sublist in data_lists]

    # 原始索引映射：列名 -> 原始数据索引
    column_index_map = {
        'iops': 0,
        'mbps': 1,
        'resp time': 4,  # resp time 原始在索引 4
        'bytes': 2,
        'read pct': 3,
        'read resp': 5,
        'write rate': 6,
        'resp max': 7,
        'resp stddev': 8,
        'queue depth': 9,
        'cpu% sys+u': 10,
        'cpu% sys': 11,
    }

    for column_name, idx in column_index_map.items():
        data_dict[column_name] = [float(item[idx]) for item in no_time_lists]

    if is_debug:
        print(data_dict)

    return data_dict


def write_excel(data_dict: Dict[str, List], path: str) -> None:
    """
    将数据字典写入 Excel 文件

    :param data_dict: 数据字典
    :param path: 输出文件路径
    """
    try:
        df = pd.DataFrame(data_dict)
        df.to_excel(path, index=False)
        print(f"The file path is : {path}")
    except Exception as e:
        print(f"Error writing Excel file: {e}")
        raise


def input_args() -> Tuple[argparse.Namespace, List[str]]:
    """
    处理输入的参数

    :return: (args, unknown_args)
    """
    arg_parse = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    arg_parse.add_argument('-v', '--version', action='version', version='2.0.0', help='Show version')
    arg_parse.add_argument('--debug', action='store_true',
                           help='Enable debug mode. \nExample:parse_totals_v2 -f <totals.html> --debug')
    arg_parse.add_argument("-C", "--output_path", help="The path can be dir or file.")
    arg_parse.add_argument("-f", "--totals_file", help='Specify the totals.html file.')
    arg_parse.add_argument('--example', help='parse_totals_v2 -f <totals.html>')

    args, un_args = arg_parse.parse_known_args()

    if len(sys.argv) == 1:
        arg_parse.print_help()
        sys.exit()

    return args, un_args


# ==================== License 相关函数 ====================

def license_check() -> None:
    """检查 License 授权"""
    license_dic = parse_license_file()
    try:
        sign = decrypt(license_dic['Sign'])
        sign_list = sign.split('#')
        uuid = sign_list[0].strip()
        date = sign_list[1].strip()
    except Exception as license_e:
        print("The license's sign is invalid!!!")
        print(license_e)
        sys.exit(1)

    if (uuid != license_dic['UUID']) or (date != license_dic['Date']):
        print('*Error*: License file is modified!')
        sys.exit(1)

    if len(sign_list) == 2:
        uuid = get_sys_uuid()
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        if sign_list[0] != uuid:
            pass  # UUID 检查已禁用
        if sign_list[1] < current_date:
            print('*Error*: License is expired!')
            print('Please check your license in /opt/parse_totals/License.dat')
            sys.exit(1)
    else:
        print('*Error*: Wrong Sign setting on license file.')
        sys.exit(1)


def parse_license_file() -> Dict[str, str]:
    """解析 License 文件"""
    license_dir = "/opt/parse_totals/"
    license_file = os.path.join(license_dir, "License.dat").replace("\\", "/")
    base_path = os.path.normpath(license_dir)

    if not os.path.exists(base_path):
        try:
            os.makedirs(base_path)
            print(f"The dir '{base_path}' create success.")
        except OSError as e:
            print(f"Error: The dir '{base_path}' create failed - {e}")

    try:
        license_dic = {}
        with open(license_file, 'r') as LF:
            for line in LF:
                match = re.match(r'^\s*(\S+)\s*:\s*(\S+)\s*$', line)
                if match:
                    license_dic[match.group(1)] = match.group(2)
        return license_dic
    except FileNotFoundError:
        print(f"ERROR: License file '{license_file}' not found.")
        sys.exit()


def decrypt(content: str) -> str:
    """AES 解密"""
    aes = AES.new(b'0CoJUm3Qyw3W3jud', AES.MODE_CBC, b'0123456789123456')
    decrypted_content = aes.decrypt(a2b_hex(content.encode('utf-8')))
    return decrypted_content.decode('utf-8')


def get_sys_uuid() -> str:
    """获取系统 UUID"""
    # Python 3.6 兼容：使用 Popen 替代 subprocess.run
    sp = subprocess.Popen('/sbin/dmidecode -s system-uuid', shell=True,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (stdout, stderr) = sp.communicate()
    stdout_list = str(stdout, 'utf-8').split('\n')
    return stdout_list[0] if stdout_list else ''


# ==================== 路径处理函数 ====================

def create_random_file(path: str) -> str:
    """
    如果文件名称已经存在，则在文件名后面添加时间戳

    :param path: 原路径
    :return: 新路径
    """
    exist_dir = "/".join(path.split('/')[:-1])
    exist_file_name = path.split('/')[-1]
    time_stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    new_path = os.path.join(exist_dir + "/" + exist_file_name[:-5] + "_" + time_stamp + ".xlsx")
    return new_path


def return_filepath(filepath: str, filename: str) -> str:
    """
    返回一个保存 xlsx 文件的路径。可处理以下几种情况：
    1. 已存在的目录路径
    2. 已存在的文件路径（指定了.xlsx 后缀）
    3. 不存在的目录或文件

    :param filepath: 输入路径
    :param filename: 文件名
    :return: 输出路径
    """
    filepath = os.path.abspath(filepath).replace("\\", "/")

    if os.path.isfile(filepath):
        if ".xlsx" in os.path.splitext(filepath)[-1]:
            return filepath
        else:
            return os.path.abspath(filepath + ".xlsx").replace("\\", "/")

    elif os.path.isdir(filepath):
        return os.path.abspath(filepath + "/" + f"{filename}.xlsx").replace("\\", "/")

    else:
        if ".xlsx" in os.path.splitext(filepath)[-1]:
            new_dir = "/".join(filepath.split('/')[:-1])
            new_file = filepath.split('/')[-1]
            if os.path.exists(new_dir):
                return os.path.abspath(new_dir + "/" + new_file).replace("\\", "/")
            else:
                os.mkdir(new_dir)
                print(f"Create new dir: {new_dir}")
                return os.path.abspath(new_dir + "/" + new_file).replace("\\", "/")
        else:
            os.mkdir(filepath)
            print(f"Create new dir: {filepath}")
            return os.path.abspath(filepath + "/" + f"{filename}.xlsx").replace("\\", "/")


def detect_file_type(input_file: str) -> str:
    """
    检测 totals.html 文件类型（file 或 block）

    :param input_file: 输入文件路径
    :return: 'file' 或 'block'
    """
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        if len(lines) > 4:
            line_5 = lines[4]
            if "<A" in line_5 and "format" in line_5:
                return 'file'
    return 'block'


def main() -> None:
    """主函数"""
    # 获取 OS UUID（预检查，不实际使用）
    get_sys_uuid()

    # 检查 license 授权（默认禁用）
    # license_check()

    # 获取参数（只解析一次）
    args_result = input_args()
    known_args = args_result[0]
    unknown_args = args_result[1]

    try:
        # 检查-f 参数
        if known_args.totals_file is None:
            print("The -f parameter is required.")
            sys.exit()

        # 检查输入文件是否存在
        if not os.path.isfile(known_args.totals_file):
            print("Input must be a file.")
            sys.exit()

        input_file = os.path.abspath(known_args.totals_file).replace("\\", "/")

        # 确定输出路径 - 默认放在 totals.html 同一目录下
        if known_args.output_path is None:
            # 获取输入文件所在目录
            input_dir = os.path.dirname(input_file)
            file_name = input_file.split('/')[-2]  # totals.html 所在目录名
            output_path = os.path.join(input_dir, f"{file_name}.xlsx").replace("\\", "/")
        else:
            file_name = input_file.split('/')[-2]
            output_path = return_filepath(known_args.output_path, file_name)

        # 如果文件已存在，生成带时间戳的新文件名
        if os.path.exists(output_path):
            output_path = create_random_file(output_path)

        # 检测文件类型并解析
        file_type = detect_file_type(input_file)

        if file_type == 'file':
            file_lists = parse_file_totals(input_file)
            file_perf_dict = file_list_to_dict(file_lists[0], file_lists[1], is_debug=known_args.debug)
            write_excel(file_perf_dict, path=output_path)
        else:
            block_lists = parse_block_totals(input_file)
            block_perf_dict = block_list_to_dict(block_lists[0], block_lists[1], is_debug=known_args.debug)
            write_excel(block_perf_dict, path=output_path)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
