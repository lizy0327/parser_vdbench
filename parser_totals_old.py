# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File       : xml_parser.py
# Time       : 2022/4/26 22:26
# Author     : lizy
# Email      : lizy0327@gmail.com
# Version    : python 3.9
# Software   : PyCharm
# Description: Welcom!!!
"""

import pandas as pd

# from pandas.io.formats.excel import ExcelWriter


def parser_totals(html_path):
    """

    :param html_path:
    :return: data dict
    """
    try:
        # 读取HTML文件
        with open(html_path, 'r') as file:
            # 包内含rd名字和运行时间等属性的列表
            title_lists = []
            # 包含最终性能数据的列表
            data_lists = []
            # print(len(file.readlines()))
            for line in file.readlines():
                if "RD=format" not in line and "avg_2-1" not in line:
                    if "name" in line or "avg_31" in line:
                        # 标题内容，处理包含<a>和<b>等标签内容
                        if "<a" in line:
                            start_tag = '<b>'
                            end_tag = '</b>'
                            start_index = line.find(start_tag) + len(start_tag)
                            end_index = line.find(end_tag)

                            if start_index != -1 and end_index != -1:
                                data = line[start_index:end_index]
                                # 去除;和.
                                data1 = data.replace(";", "")
                                # print(data1)
                                # 去除不需要的字段
                                title_list = data1.split()
                                title_list.remove("Starting")
                                title_list.remove("For")
                                title_list.remove("loops:")
                                title_lists.append(title_list)
                            else:
                                print("No <b> tag found.")
                        # 处理性能结果数据
                        else:
                            # print(line.split())
                            data_list = [item for item in line.split() if "avg" not in item]
                            data_lists.append(data_list)
                            # print(mylist)
                            # iops_list.append(mylist[1])
                            # print(iops_list)
            return title_lists, data_lists
    except SyntaxError:
        print(f"the file: {html_path} is not html format")
    except Exception as e:
        print(e)


def list_to_dict(lists):
    """
    把list数据转换成字典数据，以便写入excel
    :param lists:
    :return:
    """
    # 保存所有性能数据
    data_dict = {}

    # 保存单独的性能数据
    start_time_list = []
    start_time_dict = {}
    rd_list = []
    rd_dict = {}
    elapsed_list = []
    elapsed_dict = {}
    warmup_list = []
    warmup_dict = {}
    rate_list = []
    rate_dict = {}
    rdpct_list = []
    rdpct_dict = {}
    xfersize_list = []
    xfersize_dict = {}
    threads_list = []
    threads_dict = {}

    iops_list = []
    iops_dict = {}
    resp_list = []
    resp_dict = {}
    read_pct_list = []
    read_pct_dict = {}
    read_rate_list = []
    read_rate_dict = {}
    read_resp_list = []
    read_resp_dict = {}
    write_rate_list = []
    write_rate_dict = {}
    write_resp_list = []
    write_resp_dict = {}
    read_mbps_list = []
    read_mbps_dict = {}
    write_mbps_list = []
    write_mbps_dict = {}
    total_mbps_list = []
    total_mbps_dict = {}
    xfer_size_list = []
    xfer_size_dict = {}

    local_title_list = []
    local_data_list = []
    # print('1')
    # print(len(lists[0]))
    # print(lists[0])
    # print(lists[1])
    # 如果第1个list的总数大于第2个list，说明有未完成的rd
    if len(lists[0]) - len(lists[1]) == 1:
        lists[0].pop()
        local_title_list = lists[0]
        local_data_list = lists[1]
    elif len(lists[0]) == len(lists[1]):
        local_title_list = lists[0]
        local_data_list = lists[1]

    print(local_title_list)
    print(local_data_list)

    # 处理得到的字典
    for item in local_title_list:
        start_time_list.append(item[0])
    start_time_dict['starting time'] = start_time_list

    for item in local_title_list:
        rd_list.append(item[1].split('=')[1])
    rd_dict['rd name'] = rd_list

    for item in local_title_list:
        elapsed_list.append(int(item[2].split('=')[1]))
    elapsed_dict['elapsed'] = elapsed_list

    for item in local_title_list:
        warmup_list.append(int(item[3].split('=')[1]))
    warmup_dict['warmup'] = warmup_list

    for item in local_title_list:
        rate_list.append(item[4].split('=')[1].replace(".", ""))
    rate_dict['rate'] = rate_list

    if item[5].split('=')[0] != "rdpct":
        # 如果没有rdpct这一列
        for item in local_title_list:
            xfersize_list.append(item[5].split('=')[1])
        xfersize_dict['xfersize'] = xfersize_list

        for item in local_title_list:
            threads_list.append(int(item[6].split('=')[1]))
        threads_dict['threads'] = threads_list
    else:
        # 如果有rdpct这一列
        for item in local_title_list:
            rdpct_list.append(int(item[5].split('=')[1]))
            print()
        rdpct_dict['rdpct'] = rdpct_list

        for item in local_title_list:
            xfersize_list.append(item[6].split('=')[1])
        xfersize_dict['xfersize'] = xfersize_list

        for item in local_title_list:
            threads_list.append(int(item[7].split('=')[1]))
        threads_dict['threads'] = threads_list

    for item in local_data_list:
        iops_list.append(float(item[1]))
    iops_dict['iops'] = iops_list

    for item in local_data_list:
        resp_list.append(float(item[2]))
    resp_dict['resp'] = resp_list

    for item in local_data_list:
        read_pct_list.append(float(item[5]))
    read_pct_dict['read pct'] = read_pct_list

    for item in local_data_list:
        read_rate_list.append(float(item[6]))
    read_rate_dict['read rate'] = read_rate_list

    for item in local_data_list:
        read_resp_list.append(float(item[7]))
    read_resp_dict['read resp'] = read_resp_list

    for item in local_data_list:
        write_rate_list.append(float(item[8]))
    write_rate_dict['write rate'] = write_rate_list

    for item in local_data_list:
        write_resp_list.append(float(item[9]))
    write_resp_dict['write resp'] = write_resp_list

    for item in local_data_list:
        read_mbps_list.append(float(item[10]))
    read_mbps_dict['read mbps'] = read_mbps_list

    for item in local_data_list:
        write_mbps_list.append(float(item[11]))
    write_mbps_dict['write mbps'] = write_mbps_list

    for item in local_data_list:
        total_mbps_list.append(float(item[12]))
    total_mbps_dict['total mbps'] = total_mbps_list

    for item in local_data_list:
        xfer_size_list.append(float(item[13]))
    xfer_size_dict['xfer mbps'] = xfer_size_list

    data_dict.update(start_time_dict)
    data_dict.update(rd_dict)
    data_dict.update(elapsed_dict)
    data_dict.update(warmup_dict)
    data_dict.update(rate_dict)
    data_dict.update(xfersize_dict)
    data_dict.update(threads_dict)

    data_dict.update(iops_dict)
    data_dict.update(resp_dict)
    data_dict.update(read_pct_dict)
    data_dict.update(read_rate_dict)
    data_dict.update(read_resp_dict)
    data_dict.update(write_rate_dict)
    data_dict.update(write_resp_dict)
    data_dict.update(read_mbps_dict)
    data_dict.update(write_mbps_dict)
    data_dict.update(total_mbps_dict)
    data_dict.update(xfer_size_dict)

    # print(data_dict)
    return data_dict


def write_excel(data_dict):

    df = pd.DataFrame(data_dict)

    df.to_excel("D:\\PythonProject\\output.xlsx", index=False)

    # writer = pd.ExcelWriter(data_dict, engine='xlsxwriter')
    # for sheetname, df in data_dict.items():  # loop through `dict` of dataframes
    #     df.to_excel(writer, sheet_name=sheetname)  # send df to writer
    #     worksheet = writer.sheets[sheetname]  # pull worksheet object
    #     for idx, col in enumerate(df):  # loop through all columns
    #         series = df[col]
    #         max_len = max((
    #             series.astype(str).map(len).max(),  # len of largest item
    #             len(str(series.name))  # len of column name/header
    #         )) + 1  # adding a little extra space
    #         worksheet.set_column(idx, idx, max_len)  # set column width
    # writer.save()



    # df.to_excel("D:\\PythonProject\\output.xlsx", index=False)



    # 将DataFrame




if __name__ == '__main__':
    lists = parser_totals("D:\\PythonProject\\totals.html")

    perf_dict = list_to_dict(lists)

    write_excel(perf_dict)
