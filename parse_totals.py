# !/usr/bin/env python
# -*-coding:utf-8 -*-
"""
# File       : parse_vdbench.py
# Time       : 2023-06-20 14:44
# Author     : lizy
# Email      : lizy0327@gmail.com
# Version    : python 3.9
# Software   : PyCharm
# Description: Welcome!!!
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import time
from binascii import a2b_hex

import pandas as pd
from Cryptodome.Cipher import AES


def is_time_format(line):
    # 检查字符串长度是否满足 HH:MM:SS.SSS 格式的长度，即 12 个字符
    if len(line) < 12:
        return False

    # 检查前两个字符是否是数字且在 00-23 范围内
    if not line[:2].isdigit() or int(line[:2]) > 23:
        return False

    # 检查第三个字符是否是冒号
    if line[2] != ":":
        return False

    # 检查第四个和第五个字符是否是数字且在 00-59 范围内
    if not line[3:5].isdigit() or int(line[3:5]) > 59:
        return False

    # 检查第六个字符是否是冒号
    if line[5] != ":":
        return False

    # 检查第七个到第十二个字符是否是数字且在 00.000-59.999 范围内
    if not line[6:12].replace(".", "").isdigit() or float(line[6:12]) > 59.999:
        return False

    return True


def parse_file_totals(html_path):
    """
    此函数用来解析vdbench生成的file类型的totals.html文件，并返回2个list。
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
                """
                处理标题内容，处理包含<a>和<b>标签之间的内容
                avg_2-1,前面的2代表warmup+1时长，最后的1代表运行了总时长（warmup+elapsed）。比如avg_13-25，代表warmup是12秒，
                elapsed是13秒。如果不在rd里指定warmup，那么这里avg后面一定是2。
                """

                # 过滤RD=format这种埋数据的数据
                if "RD=format" not in line and "name" in line:
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
                            if "None" in title_list:
                                title_list.remove("None")
                            title_lists.append(title_list)
                        else:
                            print("No <b> tag found.")
                    else:
                        print("No <a> tag found.")
                # 处理性能数据，过滤掉埋数据以及检查文件的rd结果。第20个元素描述的是create的性能，第3个元素是真正的性能值
                if "avg" in line and line.split()[19] == '0.0' and line.split()[2] != '0.0' and is_time_format(line):
                    data_list = [item for item in line.split() if "avg" not in item]
                    data_lists.append(data_list)
            return title_lists, data_lists
    except SyntaxError:
        print(f"the file: {html_path} is not html format")
    except Exception as file_e:
        print(file_e)


def file_list_to_dict(title_lists, data_lists, is_debug):
    """
    把多条list数据提取相同的数据类型分别写入不同的list，并把不同的list写入字典，以便写入excel文件。
    :param is_debug:
    :param data_lists:
    :param title_lists:
    :return: perf dict
    """
    # 保存所有性能数据的字典
    data_dict = {}
    # 如果第1个list的总数大于第2个list，说明有未完成的rd，需要把第1个list最后的结果删除
    if len(title_lists) - len(data_lists) == 1:
        title_lists.pop()
        title_lists = title_lists
        data_lists = data_lists
    else:
        title_lists = title_lists
        data_lists = data_lists

    # print(title_lists)
    # print(data_lists)

    # 处理title list数据
    start_time_list = [item[0] for item in data_lists]  # 为了方便和avg数据对应，这里的开始时间使用data_list时间
    # 删除每个子列表的第一个时间元素
    temp_list1 = [sublist[1:] for sublist in title_lists]
    # 将每个子列表转换为字典
    title_dict_result = [dict(item.split('=') for item in sublist) for sublist in temp_list1]

    # 对于某些不是必须的参数，需要判断是否存在
    rd_list = [item.get('RD') for item in title_dict_result]
    elapsed_list = [int(item.get('elapsed')) if item.get('elapsed') is not None else None for item in title_dict_result]
    warmup_list = [int(item.get('warmup')) if item.get('warmup') is not None else None for item in title_dict_result]
    rate_list = [item.get('fwdrate').replace(".", "") for item in title_dict_result]
    rdpct_list = [int(item.get('rdpct')) if item.get('rdpct') is not None else None for item in title_dict_result]
    xfersize_list = [item.get('xfersize') if item.get('xfersize') is not None else None for item in title_dict_result]
    threads_list = [int(item.get('threads')) if item.get('threads') is not None else None for item in title_dict_result]

    # 把title list数据更新到字典中，以便写入cvs文件
    data_dict.update({'start time': start_time_list})
    data_dict.update({'rd name': rd_list})
    data_dict.update({'elapsed': elapsed_list})
    data_dict.update({'warmup': warmup_list})
    data_dict.update({'rate': rate_list})
    data_dict.update({'rdpct': rdpct_list})
    data_dict.update({'xfersize': xfersize_list})
    data_dict.update({'threads': threads_list})

    # 处理data list数据，把所有数字转换为float，只保留必要的性能数据即可
    columns_to_convert = [1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    # 使用列表推导式把所有性能数据转换为float类型
    converted_data = [[float(item[index]) for item in data_lists] for index in columns_to_convert]
    # 将性能数据更新到字典中
    column_names = ['iops', 'resp', 'read pct', 'read rate', 'read resp', 'write rate', 'write resp',
                    'read mbps', 'write mbps', 'total mbps', 'xfer size']
    for name, data in zip(column_names, converted_data):
        data_dict.update({name: data})

    # 判断是否打印字典数据
    if is_debug:
        print(data_dict)
    return data_dict


def parse_block_totals(html_path):
    """
    此函数用来解析vdbench生成block的totals.html文件，并返回2个list。
    :param html_path:
    :return: data list
    """
    try:
        # 读取HTML文件
        with open(html_path, 'r') as block_file:
            # 包内含rd名字和运行时间等属性的列表
            title_lists = []
            # 包含最终性能数据的列表
            data_lists = []
            for line in block_file.readlines():
                # 处理标题内容，处理包含<a>和<b>标签之间的内容
                if "name" in line:
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
                            title_list.remove("I/O")
                            if "None" in title_list:
                                title_list.remove("None")
                            if "Uncontrolled" in title_list:
                                title_list.remove("Uncontrolled")
                            if "Controlled" in title_list:
                                title_list.remove("Controlled")
                            title_lists.append(title_list)
                        else:
                            print("No <b> tag found.")
                    else:
                        print("No <a> tag found.")
                # 处理性能数据。如果这一行的开始的12个字符时间格式的，则说明是性能数据行。
                if is_time_format(line):
                    # 生成性能数据list
                    data_list = [item for item in line.split()]
                    data_lists.append(data_list)
                    """
                    测试中发现在某些情况下avg性能结果，时间和avg连到一起了（17:08:39.047avg_31-330），需要进行拆分。
                    """
                    for item in data_lists:
                        if "avg" in item[0]:  # 这种情况说明开头是17:08:39.047avg_31-330这种格式的数据，需要把时间和avg分离
                            item[0] = item[0][:12]
                        elif "avg" in item[1]:  # 这种情况说明第2列是包含了avg关键字，需要删除第2列
                            del item[1]
            return title_lists, data_lists
    except SyntaxError:
        print(f"the block file: {html_path} is not html format")
    except Exception as block_e:
        print(block_e)


def block_list_to_dict(title_lists, data_lists, is_debug):
    """
    把多条list数据提取相同的数据类型分别写入不同的list，并把不同的list写入字典，以便写入excel文件。
    :param is_debug:
    :param data_lists:
    :param title_lists:
    :return: perf dict
    """
    # 保存所有性能数据的字典
    data_dict = {}
    # 如果第1个list的总数大于第2个list，说明有未完成的rd，需要把第1个list最后的结果删除
    if len(title_lists) - len(data_lists) == 1:
        title_lists.pop()
        title_list = title_lists
        data_lists = data_lists
    else:
        title_list = title_lists
        data_lists = data_lists

    # print(title_list)
    # print(data_list)

    # 处理title list数据

    start_time_list = [item[0] for item in data_lists]  # 为了方便和avg数据对应，这里的开始时间使用data_list时间
    # 第4个元素固定为rate
    rate_list = [int(item[3]) if isinstance(item[3], int) else item[3] for item in title_lists]
    # 删除第1个元素的列表
    temp_list1 = [sublist[1:] for sublist in title_lists]
    # 删除第2个（rate)和第3个（rate的值）元素后的列表
    temp_list2 = [item[:1] + item[3:] for item in temp_list1]

    # 将剩下的list转换为字典
    title_dict_result = [dict(item.split('=') for item in sublist) for sublist in temp_list2]

    # 由于RD使用的参数不同，会导致title内容也会有差异，以下参数不是rd必须的，所以需要判断是否存在
    rd_list = [item.get('RD') for item in title_dict_result]
    elapsed_list = [int(item.get('elapsed')) if item.get('elapsed') is not None else None for item in title_dict_result]
    warmup_list = [int(item.get('warmup')) if item.get('warmup') is not None else None for item in title_dict_result]
    rdpct_list = [int(item.get('rdpct')) if item.get('rdpct') is not None else None for item in title_dict_result]
    xfersize_list = [item.get('xfersize', None) for item in title_dict_result]
    threads_list = [int(item.get('threads')) if item.get('threads') is not None else None for item in title_dict_result]

    # 把title list数据更新到字典中，以便写入cvs文件
    data_dict.update({'start time': start_time_list})
    data_dict.update({'rd name': rd_list})
    data_dict.update({'rate': rate_list})
    data_dict.update({'elapsed': elapsed_list})
    data_dict.update({'warmup': warmup_list})
    data_dict.update({'rdpct': rdpct_list})
    data_dict.update({'xfersize': xfersize_list})
    data_dict.update({'threads': threads_list})

    # 处理性能数据

    # 删除每个子列表的第一个时间元素，时间使用title_list数据
    no_time_lists = [sublist[1:] for sublist in data_lists]
    # 定一个12个元素
    column_names = ['iops', 'mbps', 'bytes', 'read pct', 'resp time', 'read resp', 'write rate',
                    'resp max', 'resp stddev', 'queue depth', 'cpu% sys+u', 'cpu% sys']
    # 性能数据每一列都是固定的数值，所以可以根据顺序对每一列进行赋值操作
    for idx, column_name in enumerate(column_names):
        column_values = [float(item[idx]) for item in no_time_lists]
        data_dict.update({column_name: column_values})

    # 上面的代码是优化的下面复杂的代码，暂时保留注释，以防后面TroubltShooting使用，下个版本删除。
    # if is_time_format(data_list[0][0]):
    #     # 如果第1个元素是时间格式，那么iops应该从list[1]开始
    #     iops_list = [float(item[1]) for item in data_list]
    #     mbps_list = [float(item[2]) for item in data_list]
    #     block_size_list = [float(item[3]) for item in data_list]
    #     read_pct_list = [float(item[4]) for item in data_list]
    #     resp_time_list = [float(item[5]) for item in data_list]
    #     read_resp_time_list = [float(item[6]) for item in data_list]
    #     write_resp_time_list = [float(item[7]) for item in data_list]
    #     resp_max_list = [float(item[8]) for item in data_list]
    #     resp_stddev_list = [float(item[9]) for item in data_list]
    #     queue_depth_list = [float(item[10]) for item in data_list]
    #     cpu1_list = [float(item[11]) for item in data_list]
    #     cpu2_list = [float(item[12]) for item in data_list]
    #
    #     # 把data list数据更新到字典中，以便写入cvs文件
    #     data_dict.update({'iops': iops_list})
    #     data_dict.update({'mbps': mbps_list})
    #     data_dict.update({'block size': block_size_list})
    #     data_dict.update({'read pct': read_pct_list})
    #     data_dict.update({'resp time': resp_time_list})
    #     data_dict.update({'read resp time': read_resp_time_list})
    #     data_dict.update({'write rate time': write_resp_time_list})
    #     data_dict.update({'resp max': resp_max_list})
    #     data_dict.update({'resp stddev': resp_stddev_list})
    #     data_dict.update({'queue depth': queue_depth_list})
    #     data_dict.update({'cpu% sys+u': cpu1_list})
    #     data_dict.update({'cpu% sys': cpu2_list})

    # 判断是否打印字典数据
    if is_debug:
        print(data_dict)
    return data_dict


def write_excel(data_dict, path):
    os.path.abspath(path.replace("\\", "/"))
    df = pd.DataFrame(data_dict)
    df.to_excel(path, index=False)
    print(f"The file path is : {path}")


def intput_args():
    """
    处理输入的参数
    :return:
    """
    # 创建 ArgumentParse 对象，使用formatter_class参数帮助文本的格式化方式为原始文本格式。这样可以保留文本中的换行符。
    arg_parse = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    # 添加版本信息
    arg_parse.add_argument('-v', '--version', action='version', version='3.1.1', help='Show version')
    # 添加 debug 参数，如果添加了debug参数则为True，否则为False
    arg_parse.add_argument('--debug', action='store_true',
                           help='Enable debug mode. \nExample:parse_totals -f <totals.html> --debug')
    # 定义输出目录参数
    arg_parse.add_argument("-C", "--output_path", help="The path can be dir or file.")
    # 定义解析文件参数
    arg_parse.add_argument("-f", "--totals_file", help='Specify the totals.html file.')
    arg_parse.add_argument('--example', help='parse_totals -f <totals.html>')
    # 解析命令行参数，返回1个元组，args包含了所有已知参数，un_args包含了未知参数列表
    args, un_args = arg_parse.parse_known_args()

    # 如果没有任何参数，打印帮助
    if len(sys.argv) == 1:
        arg_parse.print_help()
        sys.exit()
    elif len(sys.argv) > 1:
        return args, un_args


# License check
def license_check():
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

    # Check license file is modified or not.
    if (uuid != license_dic['UUID']) or (date != license_dic['Date']):
        print('*Error*: License file is modified!')
        sys.exit(1)

    # Check UUID and effective date invalid or not.
    if len(sign_list) == 2:
        uuid = get_sys_uuid()
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        # Must run this script under specified UUID.
        if sign_list[0] != uuid:
            # print('*Error*: Invalid host!')
            # sys.exit(1)
            pass
        # Current time must be before effective date.
        if sign_list[1] < current_date:
            print('*Error*: License is expired!')
            sys.exit(1)
    else:
        print('*Error*: Wrong Sign setting on license file.')
        sys.exit(1)


def parse_license_file():
    try:
        license_dic = {}
        license_file = './License.dat'
        with open(license_file, 'r') as LF:
            for line in LF.readlines():
                if re.match('^\s*(\S+)\s*:\s*(\S+)\s*$', line):
                    my_match = re.match('^\s*(\S+)\s*:\s*(\S+)\s*$', line)
                    license_dic[my_match.group(1)] = my_match.group(2)
        return license_dic
    except FileNotFoundError:
        print("License file is not found.")
        sys.exit()


def decrypt(content):
    aes = AES.new(b'0CoJUm3Qyw3W3jud', AES.MODE_CBC, b'0123456789123456')
    decrypted_content = aes.decrypt(a2b_hex(content.encode('utf-8')))
    return decrypted_content.decode('utf-8')


def get_sys_uuid():
    sp = subprocess.Popen('/sbin/dmidecode -s system-uuid', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    (stdout, stderr) = sp.communicate()
    stdout_list = str(stdout, 'utf-8').split('\n')
    return stdout_list[0]


def create_random_file(path):
    """
    如果文件名称已经存在，则在文件名后面添加随机数
    :param path:
    :return:
    """
    exist_dir = "/".join(path.split('/')[:-1])
    exist_file_name = path.split('/')[-1]
    # 生成随机数字戳
    time_stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    # 拼接新的路径
    new_path = os.path.join(exist_dir + "/" + exist_file_name.split('.')[0] + "_" + time_stamp + ".xlsx")
    return new_path


def return_filepath(filepath):
    """
    返回一个保存xlsx文件的目录。此函数可以处理以下几种情况：
    1.可以接收已经存在的目录路径
    2.可以接收已经存在的文件路径
    3.可以接收不存在的目录文件或文件，或二者只有一个存在的情况
    :param filepath:
    :return:
    """
    # 把路径所有反斜杠转换为正斜杠，避免出现windows和linux路径斜杠不一样的问题
    filepath = os.path.abspath(filepath).replace("\\", "/")

    # 如果是一个文件，则根据文件后缀名进行判断处理逻辑
    if os.path.isfile(filepath):
        # 如果路径中包含.xlsx扩展名（有点号），直接返回路径
        if ".xlsx" in os.path.splitext(filepath)[-1]:
            return filepath
        # 如果是一个文件，则自动根据文件生成新的后缀名称文件
        else:
            return os.path.abspath(filepath + ".xlsx").replace("\\", "/")
    # 如果是一个目录，则在此目录下生成totals.xlsx文件
    elif os.path.isdir(filepath):
        return os.path.abspath(filepath + "/" + "totals.xlsx").replace("\\", "/")
    else:
        # 如果路径里包含.xlsx后缀，则同时创建目录和文件
        if ".xlsx" in os.path.splitext(filepath)[-1]:
            # 根据文件名称，创建目录
            new_dir = "/".join(filepath.split('/')[:-1])
            new_file = filepath.split('/')[-1]
            # 如果文件是不存在的，但是目录已经存在了
            if os.path.exists(new_dir):
                return os.path.abspath(new_dir + "/" + new_file).replace("\\", "/")
            # 无论目录还是文件都是新的
            else:
                os.mkdir(new_dir)
                print(f"Create new dir: {new_dir}")
                return os.path.abspath(new_dir + "/" + new_file).replace("\\", "/")
        # 路径里没有.xlsx后缀，只创建新目录
        else:
            os.mkdir(filepath)
            print(f"Create new dir: {filepath}")
            return os.path.abspath(filepath + "/" + "totals.xlsx").replace("\\", "/")


if __name__ == '__main__':
    # 获取OS UUID
    get_sys_uuid()
    # 检查license授权
    license_check()

    # 获取所有参数
    known_args = intput_args()[0]
    unknown_args = intput_args()[1]
    try:
        # 因为-f参数是必选，有必要判断是否非空
        if known_args.totals_file is None:
            print("The -f parameter is required.")
            sys.exit()
        # 被解析路径必须为文件格式
        if os.path.isfile(known_args.totals_file):
            input_file = os.path.abspath(known_args.totals_file).replace("\\", "/")
        else:
            print("intput must be a file.")
            sys.exit()
        # 如果没有指定-C参数，则在同名目录下产生文件
        if known_args.output_path is None:
            output_path = os.path.abspath(os.getcwd() + "/" + "totals.xlsx").replace("\\", "/")
        else:
            output_path = return_filepath(known_args.output_path)
        # 判断文件是否存在
        if os.path.exists(output_path):
            output_path = create_random_file(output_path)

        # 执行文件解析和输出,读取HTML文件
        with open(input_file, 'r') as file:
            # 文件类型性能测试
            if "<A" and "format" in file.readlines()[4]:
                file_lists = parse_file_totals(input_file)
                file_perf_dict = file_list_to_dict(file_lists[0], file_lists[1], is_debug=known_args.debug)
                write_excel(file_perf_dict, path=output_path)
            else:
                # 块设备类型性能测试
                block_lists = parse_block_totals(input_file)
                block_perf_dict = block_list_to_dict(block_lists[0], block_lists[1], is_debug=known_args.debug)
                write_excel(block_perf_dict, path=output_path)
    except Exception as e:
        print(e)
