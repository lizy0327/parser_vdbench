# !/usr/bin/env python3
# -*-coding:utf-8 -*-

"""
# File       : xml_parser.py
# Time       : 2023/08/28 22:48
# Author     : lizy
# Email      : lizy0327@gmail.com
# Version    : python 3.8
# Software   : PyCharm
# Description: Welcom!!!
"""

import re
import sys
import datetime
import subprocess
from Cryptodome.Cipher import AES
from binascii import a2b_hex


# License check
def license_check():
    license_dic = parse_license_file()
    print(license_dic)
    sign = decrypt(license_dic['Sign'])
    sign_list = sign.split('#')
    mac = sign_list[0].strip()
    date = sign_list[1].strip()
    # Check license file is modified or not.
    if (mac != license_dic['MAC']) or (date != license_dic['Date']):
        print('*Error*: License file is modified!')
        sys.exit(1)

    # Check MAC and effective date invalid or not.
    if len(sign_list) == 2:
        mac = get_mac()
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        # print(current_date)
        # Must run this script under specified MAC.
        if sign_list[0] != mac:
            print('*Error*: Invalid host!')
            sys.exit(1)

        # Current time must be before effective date.
        if sign_list[1] < current_date:
            print('*Error*: License is expired!')
            sys.exit(1)
    else:
        print('*Error*: Wrong Sign setting on license file.')
        sys.exit(1)


def parse_license_file():
    license_dic = {}
    license_file = 'opt/parse_totals/License.dat'
    with open(license_file, 'r') as LF:
        for line in LF.readlines():
            if re.match('^\s*(\S+)\s*:\s*(\S+)\s*$', line):
                my_match = re.match('^\s*(\S+)\s*:\s*(\S+)\s*$', line)
                license_dic[my_match.group(1)] = my_match.group(2)
    return license_dic


def decrypt(content):
    aes = AES.new(b'0CoJUm3Qyw3W3jud', AES.MODE_CBC, b'0123456789123456')
    decrypted_content = aes.decrypt(a2b_hex(content.encode('utf-8')))
    return decrypted_content.decode('utf-8')


def get_mac():
    mac = ''
    SP = subprocess.Popen('/sbin/ifconfig', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    (stdout, stderr) = SP.communicate()
    for line in str(stdout, 'utf-8').split('\n'):
        if re.match('^\s*ether\s+(\S+)\s+.*$', line):
            my_match = re.match('^\s*ether\s+(\S+)\s+.*$', line)
            mac = my_match.group(1)
            break
    mac = '00:50:56:81:4e:a2'
    return mac


# Main function.
def function():
    print('I am an EDA tool!')


if __name__ == '__main__':
    license_check()
    function()
