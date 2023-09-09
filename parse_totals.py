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
import os
import sys
import argparse
import re
import time
import datetime
import pandas as pd
from Cryptodome.Cipher import AES
from binascii import a2b_hex
import subprocess


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
                # 过滤重新埋数据的RD
                if "RD=format" not in line and "avg_2-1" not in line and "fill" not in line:
                    '''
                    avg_2-1,前面的2代表warmup+1时长，最后的1代表运行了总时长（warmup+elapsed）。比如avg_13-25，代表warmup是12秒，
                    elapsed是13秒。
                    '''
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
                                title_lists.append(title_list)
                            else:
                                print("No <b> tag found.")
                        else:
                            print("No <a> tag found.")
                    # 处理性能数据
                    if is_time_format(line):
                        data_list = [item for item in line.split() if "avg" not in item]
                        data_lists.append(data_list)
            return title_lists, data_lists
    except SyntaxError:
        print(f"the file: {html_path} is not html format")
    except Exception as file_e:
        print(file_e)


def file_list_to_dict(title_list, data_list, is_debug):
    """
    把多条list数据提取相同的数据类型分别写入不同的list，并把不同的list写入字典，以便写入excel文件。
    :param is_debug:
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
    else:
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
                            if "Uncontrolled" in title_list:
                                title_list.remove("Uncontrolled")
                            if "Controlled" in title_list:
                                title_list.remove("Controlled")
                            title_list.remove("rate:")
                            title_lists.append(title_list)
                        else:
                            print("No <b> tag found.")
                    else:
                        print("No <a> tag found.")
                # 处理性能数据
                if is_time_format(line):
                    data_list = [item for item in line.split() if "avg" not in item]
                    data_lists.append(data_list)
            return title_lists, data_lists
    except SyntaxError:
        print(f"the block file: {html_path} is not html format")
    except Exception as block_e:
        print(block_e)


def block_list_to_dict(title_list, data_list, is_debug):
    """
    把多条list数据提取相同的数据类型分别写入不同的list，并把不同的list写入字典，以便写入excel文件。
    :param is_debug:
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
    else:
        title_list = title_list
        data_list = data_list

    # print(title_list)
    # print(data_list)

    # 处理title list数据
    start_time_list = [item[0] for item in title_list]
    rd_list = [item[1].split('=')[1] for item in title_list]
    rate_list = [item[2] for item in title_list]
    elapsed_list = [int(item[3].split('=')[1]) for item in title_list]
    warmup_list = [int(item[4].split('=')[1]) for item in title_list]
    threads_list = [int(item[5].split('=')[1]) for item in title_list]

    # 更新title字典数据
    data_dict.update({'start time': start_time_list})
    data_dict.update({'rd name': rd_list})
    data_dict.update({'rate': rate_list})
    data_dict.update({'elapsed': elapsed_list})
    data_dict.update({'warmup': warmup_list})
    data_dict.update({'threads': threads_list})

    # 处理data list数据
    iops_list = [float(item[0]) for item in data_list]
    mbps_list = [float(item[1]) for item in data_list]
    block_size_list = [float(item[2]) for item in data_list]
    read_pct_list = [float(item[3]) for item in data_list]
    resp_time_list = [float(item[4]) for item in data_list]
    read_resp_time_list = [float(item[5]) for item in data_list]
    write_resp_time_list = [float(item[6]) for item in data_list]
    resp_max_list = [float(item[7]) for item in data_list]
    resp_stddev_list = [float(item[8]) for item in data_list]
    queue_depth_list = [float(item[9]) for item in data_list]
    cpu1_list = [float(item[10]) for item in data_list]
    cpu2_list = [float(item[11]) for item in data_list]

    # 更新data字典数据
    data_dict.update({'iops': iops_list})
    data_dict.update({'mbps': mbps_list})
    data_dict.update({'block size': block_size_list})
    data_dict.update({'read pct': read_pct_list})
    data_dict.update({'resp time': resp_time_list})
    data_dict.update({'read resp time': read_resp_time_list})
    data_dict.update({'write rate time': write_resp_time_list})
    data_dict.update({'resp max': resp_max_list})
    data_dict.update({'resp stddev': resp_stddev_list})
    data_dict.update({'queue depth': queue_depth_list})
    data_dict.update({'cpu% sys+u': cpu1_list})
    data_dict.update({'cpu% sys': cpu2_list})

    # 判断是否打印字典数据
    if is_debug:
        print(data_dict)
    return data_dict


def write_excel(data_dict, output_path, result_name):
    os.path.abspath(output_path.replace("\\", "/"))
    df = pd.DataFrame(data_dict)

    # 如果文件已存在，会生成新的文件
    if os.path.exists(output_path + "/" + result_name + ".xlsx"):
        # 生成随机数字戳
        time_stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        # 拼接新的路径
        new_path = os.path.join(output_path + "/" + result_name + "_" + time_stamp + ".xlsx")
        df.to_excel(new_path, index=False)
        print(f"The file path is : {new_path}")
    else:
        file_path = output_path + "/" + result_name + ".xlsx"
        df.to_excel(file_path, index=False)
        print(f"The file path is : {file_path}")


def intput_args():
    """
    处理输入的参数
    :return:
    """
    # 创建 ArgumentParse 对象，使用formatter_class参数帮助文本的格式化方式为原始文本格式。这样可以保留文本中的换行符。
    arg_parse = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    # 添加版本信息
    arg_parse.add_argument('-v', '--version', action='version', version='3.0', help='Show version')
    # 添加 debug 参数，如果添加了debug参数则为True，否则为False
    arg_parse.add_argument('--debug', action='store_true',
                            help='Enable debug mode. \nExample:parse_totals -f <totals.html> --debug')
    # 定义输出目录参数
    arg_parse.add_argument("-C", "--output_dir", help="Specify the output directory.")
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
        print("License file is not found")
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


if __name__ == '__main__':
    # 获取OS UUID
    get_sys_uuid()
    # 检查license授权
    # license_check()

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

        # 如果不指定输出目录，则在同目录下生成输出文件
        if known_args.output_dir is None:
            output_dir = os.path.dirname(input_file)
        else:
            # 文件输出路径必须为目录格式
            if os.path.isdir(known_args.output_dir):
                output_dir = os.path.abspath(known_args.output_dir).replace("\\", "/")
            else:
                print("output must be a dir.")
                sys.exit()

        # 执行文件解析和输出,读取HTML文件
        with open(input_file, 'r') as file:
            # 文件类型性能测试
            if "<A" and "format" in file.readlines()[4]:
                file_lists = parse_file_totals(input_file)
                file_perf_dict = file_list_to_dict(file_lists[0], file_lists[1], is_debug=known_args.debug)
                write_excel(file_perf_dict, output_path=output_dir,
                            result_name=input_file.split("/")[-1].split(".")[0])
            else:
                # 块设备类型性能测试
                block_lists = parse_block_totals(input_file)
                block_perf_dict = block_list_to_dict(block_lists[0], block_lists[1], is_debug=known_args.debug)
                write_excel(block_perf_dict, output_path=output_dir,
                            result_name=input_file.split("/")[-1].split(".")[0])
    except Exception as e:
        print(e)
