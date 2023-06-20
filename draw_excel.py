# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File       : xml_parser.py
# Time       : 2023/6/15 22:26
# Author     : lizy
# Email      : lizy0327@gmail.com
# Version    : python 3.9
# Software   : PyCharm
# Description: Welcom!!!
"""

import pandas as pd
import matplotlib.pyplot as plt
import xlwings as xw


def draw_excel():
    df = pd.read_excel(r'D:\\PythonProject\\test.xlsx')
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    x = df['threads']
    y1 = df['iops']
    y2 = df['resp']

    figure = plt.figure()

    plt.bar(x, y1, color='red', label='iops')
    plt.legend(loc='upper left')
    plt.twinx()
    plt.plot(x, y2, color='blue', label='resp')
    plt.legend(loc='upper right')
    with xw.App(visible=False, add_book=False) as app:
        workbook = app.books.open(r'D:\\PythonProject\\test.xlsx')
        worksheet = workbook.sheets[0]
        worksheet.pictures.add(figure, left=200)
        workbook.save()
        workbook.close()


    # plt.plot(x, y1, color='black', linewidth=4)
    # plt.bar(x, y2, color='blue')
    #
    # plt.show()


if __name__ == '__main__':
    draw_excel()
