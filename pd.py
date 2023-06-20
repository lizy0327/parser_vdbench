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

# 创建数据
data = {'Column1': [1, 2, 3, 4, 5],
        'Column2': ['A', 'B', 'C', 'D', 'E']}

# 创建DataFrame
df = pd.DataFrame(data)

# 创建Excel写入器
# writer = pd.ExcelWriter('output.xlsx')

# 将DataFrame写入Excel文件
df.to_excel('output.xlsx', index=False)

# 保存文件


