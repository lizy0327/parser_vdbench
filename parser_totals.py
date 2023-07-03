# !/usr/bin/env python
# -*-coding:utf-8 -*-
"""
# File       : parser_vdbench.py
# Time       : 2023-06-20 14:44
# Author     : lizy
# Email      : lizy0327@gmail.com
# Version    : python 3.9
# Software   : PyCharm
# Description: Welcom!!!
"""
import os
import sys
import argparse
import time
import pandas as pd


def parser_totals(html_path):
    """
    此函数用来解析vdbench生成的totals.html文件，并返回2个list。
    :param html_path:
    :return: data list
    """
    try:
        # 读取HTML文件
        with open(html_path, 'r') as file:
            # 包内含rd名字和运行时间等属性的列表
            title_lists = []
            # 包含最终性能数据的列表
            data_lists = []
            for line in file.readlines():
                # 过滤埋数据的RD
                if "RD=format" not in line and "avg_2-1" not in line:
                    if "name" in line or "avg_31" in line:
                        # 处理标题内容，处理包含<a>和<b>标签之间的内容
                        if "<a" in line:
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
                                title_list.remove("Starting")
                                title_list.remove("For")
                                title_list.remove("loops:")
                                title_lists.append(title_list)
                            else:
                                print("No <b> tag found.")
                        # 处理性能数据
                        else:
                            data_list = [item for item in line.split() if "avg" not in item]
                            data_lists.append(data_list)
            return title_lists, data_lists
    except SyntaxError:
        print(f"the file: {html_path} is not html format")
    except Exception as e:
        print(e)


def list_to_dict(title_list, data_list):
    """
    把多条list数据提取相同的数据类型分别写入不同的list，并把不同的list写入字典，以便写入excel文件。
    :param data_list:
    :param title_list:
    :return: perf dict
    """
    # 保存所有性能数据的字典
    data_dict = {}
    # 如果第1个list的总数大于第2个list，说明有未完成的rd，需要把第1个list最后的结果删除
    if len(title_list) - len(data_list) == 1:
        title_list.pop()
        title_list = title_list
        data_list = data_list

    # print(title_list)
    # print(data_list)

    # 处理title list数据
    start_time_list = [item[0] for item in title_list]
    rd_list = [item[1].split('=')[1] for item in title_list]
    elapsed_list = [int(item[2].split('=')[1]) for item in title_list]
    warmup_list = [int(item[3].split('=')[1]) for item in title_list]
    rate_list = [item[4].split('=')[1].replace(".", "") for item in title_list]
    rdpct_list = [int(item[5].split('=')[1]) if len(item) == 8 else 'no rdpct' for item in title_list]
    xfersize_list = [item[6].split('=')[1] if len(item) == 8 else item[5].split('=')[1] for item in title_list]
    threads_list = [int(item[7].split('=')[1]) if len(item) == 8 else int(item[6].split('=')[1]) for item in
                    title_list]

    # 处理data list数据
    iops_list = [float(item[1]) for item in data_list]
    resp_list = [float(item[2]) for item in data_list]
    read_pct_list = [float(item[5]) for item in data_list]
    read_rate_list = [float(item[6]) for item in data_list]
    read_resp_list = [float(item[7]) for item in data_list]
    write_rate_list = [float(item[8]) for item in data_list]
    write_resp_list = [float(item[9]) for item in data_list]
    read_mbps_list = [float(item[10]) for item in data_list]
    write_mbps_list = [float(item[11]) for item in data_list]
    total_mbps_list = [float(item[12]) for item in data_list]
    xfer_size_list = [float(item[13]) for item in data_list]

    # 更新title字典数据
    data_dict.update({'start time': start_time_list})
    data_dict.update({'rd name': rd_list})
    data_dict.update({'elapsed': elapsed_list})
    data_dict.update({'warmup': warmup_list})
    data_dict.update({'rate': rate_list})

    if rdpct_list[0] != 'no rdpct':
        data_dict.update({'rdpct': rdpct_list})

    data_dict.update({'xfersize': xfersize_list})
    data_dict.update({'threads': threads_list})

    # 更新data字典数据
    data_dict.update({'iops': iops_list})
    data_dict.update({'resp': resp_list})
    data_dict.update({'read pct': read_pct_list})
    data_dict.update({'read rate': read_rate_list})
    data_dict.update({'read resp': read_resp_list})
    data_dict.update({'write rate': write_rate_list})
    data_dict.update({'write resp': write_resp_list})
    data_dict.update({'read mbps': read_mbps_list})
    data_dict.update({'write mbps': write_mbps_list})
    data_dict.update({'total mbps': total_mbps_list})
    data_dict.update({'xfer size': xfer_size_list})

    # 如果没有--debug标识，则不打印字典信息
    if intput_args()[-1]:
        print(data_dict)
    return data_dict


def write_excel(data_dict, output_path, result_name):
    os.path.abspath(output_path.replace("\\", "/"))
    df = pd.DataFrame(data_dict)

    # 如果文件已存在，会生成新的文件
    if os.path.exists(os.path.dirname(output_path) + "/" + result_name + ".xlsx"):
        # 生成随机数字戳
        time_stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        # 拼接新的路径
        new_path = os.path.join(os.path.dirname(output_path) + "/" + result_name + "_" + time_stamp + ".xlsx")
        df.to_excel(new_path, index=False)
        print(f"The file path is : {new_path}")
    else:
        file_path = os.path.dirname(output_path) + "/" + result_name + ".xlsx"
        df.to_excel(file_path, index=False)
        print(f"The file path is : {file_path}")


def is_valid_filename(filename):
    """
    检查文件名是否合法，暂未使用。
    :param filename:
    :return:
    """
    # 检查是否包含斜杠
    if '/' in filename:
        return False

    if '\\' in filename:
        return False

    # 检查是否包含空字符或空白字符
    if any(char.isspace() for char in filename):
        return False

    # 检查是否包含特殊字符
    special_characters = set('/\n\t\r\v\f')
    if any(char in special_characters for char in filename):
        return False

    if sys.platform == 'win32' and ':' not in filename:
        return False
    elif sys.platform == 'linux' and ':' in filename:
        return False

    # 文件名合法
    return True


def convert_path(path):
    # 将路径分隔符替换为Linux风格的斜杠，并在末尾加上斜杠，保持格式一致
    absolute_path = os.path.abspath(path).replace("\\", "/")

    if not absolute_path.endswith("/"):
        absolute_path += "/"
    return absolute_path


def intput_args():
    """
    用来处理输入的参数
    :return:
    """

    # 创建 ArgumentParser 对象，使用formatter_class参数帮助文本的格式化方式为原始文本格式。这样可以保留文本中的换行符。
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    # 添加版本信息
    arg_parser.add_argument('-v', '--version', action='version', version='1.3.0', help='Show version')
    # 添加 debug 参数，如果添加了debug参数则为True，否则为False
    arg_parser.add_argument('--debug', action='store_true',
                            help='Enable debug mode. \nExample:parser_totals <totals.html> --debug')
    arg_parser.add_argument('--example', help='parser_totals <totals.html>')
    # 解析命令行参数，known_args包含除--debug以外的所有参数
    args, known_args = arg_parser.parse_known_args()

    # 如果没有任何参数，打印帮助
    if len(sys.argv) == 1:
        arg_parser.print_help()
        sys.exit()
    # 判断是否启用了 debug 模式
    elif args.debug:
        return known_args, True
    else:
        return known_args, False


if __name__ == '__main__':
    # 只允许传入1个参数，默认会在文件同目录下生成xlsx文件
    if len(intput_args()[0]) == 1:
        if os.path.isfile(intput_args()[0][0]):
            # 获取参数列表里的第1个参数
            input_path = os.path.abspath(intput_args()[0][0]).replace("\\", "/")
            lists = parser_totals(input_path)
            perf_dict = list_to_dict(lists[0], lists[1])
            write_excel(perf_dict, output_path=input_path, result_name=input_path.split("/")[-1].split(".")[0])
        else:
            print("there is no such as file.")
    else:
        print("param is invalid, only one param.")
