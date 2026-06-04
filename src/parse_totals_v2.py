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
import glob
import logging
import os
import re
import subprocess
import sys
import time
from binascii import a2b_hex
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from Crypto.Cipher import AES

# ==================== 常量配置 ====================

VERSION = "2.0.6"
LICENSE_DIR = "/opt/parse_totals/"
LICENSE_FILE = os.path.join(LICENSE_DIR, "License.dat")
AES_KEY = b"0CoJUm3Qyw3W3jud"
AES_IV = b"0123456789123456"
TIME_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")

# HTML 解析关键词
REMOVE_KEYWORDS_FILE = ["Starting", "For", "loops:", "None"]
REMOVE_KEYWORDS_BLOCK = ["Starting", "For", "loops:", "I/O", "None", "Uncontrolled", "Controlled"]

# 性能数据列索引 (file 模式)
FILE_PERF_COLUMNS = {
    "iops": 1,
    "resp": 2,
    "read pct": 5,
    "read rate": 6,
    "read resp": 7,
    "write rate": 8,
    "write resp": 9,
    "read mbps": 10,
    "write mbps": 11,
    "total mbps": 12,
    "xfer size": 13,
}

# 性能数据列索引 (block 模式)
BLOCK_PERF_COLUMNS = {
    "iops": 0,
    "mbps": 1,
    "resp": 4,
    "bytes": 2,
    "read pct": 3,
    "read resp": 5,
    "write rate": 6,
    "resp max": 7,
    "resp stddev": 8,
    "queue depth": 9,
    "cpu% sys+u": 10,
    "cpu% sys": 11,
}

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ==================== 工具函数 ====================


def is_time_format(line: str) -> bool:
    """检查字符串是否为 HH:MM:SS.SSS 时间格式"""
    if len(line) < 12:
        return False
    return bool(TIME_PATTERN.match(line[:12]))


def extract_html_title(line: str, remove_keywords: List[str]) -> Optional[List[str]]:
    """
    从 HTML 行中提取标题列表

    :param line: HTML 行
    :param remove_keywords: 需要移除的关键词
    :return: 标题列表，如果提取失败返回 None
    """
    if "name" not in line or "<a" not in line or "RD=format" in line:
        return None

    start_tag = "<b>"
    end_tag = "</b>"
    start_index = line.find(start_tag) + len(start_tag)
    end_index = line.find(end_tag)

    if start_index == -1 or end_index == -1:
        return None

    data = line[start_index:end_index].replace(";", "")
    title_list = [item for item in data.split() if item not in remove_keywords]
    return title_list if title_list else None


def parse_time_value(value: str) -> Optional[float]:
    """安全解析时间值"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# ==================== File 模式解析 ====================


def parse_file_totals(html_path: str) -> Tuple[List[List[str]], List[List[str]]]:
    """
    解析 vdbench 生成的 file 类型的 totals.html 文件

    :param html_path: HTML 文件路径
    :return: (title_lists, data_lists)
    """
    title_lists = []
    data_lists = []

    try:
        with open(html_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                # 提取标题
                title = extract_html_title(line, REMOVE_KEYWORDS_FILE)
                if title:
                    title_lists.append(title)

                # 提取性能数据
                if "avg" in line and is_time_format(line):
                    parts = line.split()
                    if len(parts) > 19 and parts[19] == "0.0" and parts[2] != "0.0":
                        data_list = [item for item in parts if "avg" not in item]
                        data_lists.append(data_list)

        return title_lists, data_lists

    except FileNotFoundError:
        logger.error(f"File not found: {html_path}")
        raise
    except UnicodeDecodeError:
        logger.error(f"Encoding error in file: {html_path}")
        raise


def file_list_to_dict(
    title_lists: List[List[str]], data_lists: List[List[str]], is_debug: bool = False
) -> Dict[str, List]:
    """
    将 file 模式的标题和数据转换为字典

    :param title_lists: 标题列表
    :param data_lists: 数据列表
    :param is_debug: 是否打印调试信息
    :return: 性能数据字典
    """
    # 处理未完成的 rd
    if len(title_lists) - len(data_lists) == 1:
        title_lists.pop()

    # 提取时间列
    start_time_list = [item[0] for item in data_lists]

    # 解析标题为字典
    temp_list = [sublist[1:] for sublist in title_lists]
    title_dicts = [
        dict(item.split("=") for item in sublist if "=" in item)
        for sublist in temp_list
    ]

    # 构建数据字典
    data_dict: Dict[str, List] = {
        "start time": start_time_list,
        "rd name": [d.get("RD") for d in title_dicts],
        "elapsed": [_safe_int(d.get("elapsed")) for d in title_dicts],
        "warmup": [_safe_int(d.get("warmup")) for d in title_dicts],
        "rate": [d.get("fwdrate", "").replace(".", "") for d in title_dicts],
        "rdpct": [_safe_int(d.get("rdpct")) for d in title_dicts],
        "xfersize": [d.get("xfersize") for d in title_dicts],
        "threads": [d.get("threads") for d in title_dicts],
    }

    # 添加性能数据列
    for col_name, col_idx in FILE_PERF_COLUMNS.items():
        data_dict[col_name] = [_safe_float(item[col_idx]) for item in data_lists]
        # 在 iops 列后添加 mbps 列 (与 total mbps 一致)
        if col_name == "iops":
            data_dict["mbps"] = [_safe_float(item[FILE_PERF_COLUMNS["total mbps"]]) for item in data_lists]

    if is_debug:
        logger.debug(f"File data dict: {data_dict}")

    return data_dict


# ==================== Block 模式解析 ====================


def parse_block_totals(html_path: str) -> Tuple[List[List[str]], List[List[str]]]:
    """
    解析 vdbench 生成 block 的 totals.html 文件

    :param html_path: HTML 文件路径
    :return: (title_lists, data_lists)
    """
    title_lists = []
    data_lists = []

    try:
        with open(html_path, "r", encoding="utf-8") as block_file:
            for line in block_file:
                line = line.strip()

                # 提取标题
                title = extract_html_title(line, REMOVE_KEYWORDS_BLOCK)
                if title:
                    title_lists.append(title)

                # 提取性能数据
                if is_time_format(line):
                    data_list = line.split()
                    data_lists.append(data_list)

        # 处理时间和 avg 连在一起的特殊情况
        cleaned_data = []
        for item in data_lists:
            if item and "avg" in item[0]:
                item[0] = item[0][:12]
            if len(item) > 1 and "avg" in item[1]:
                item = item[:1] + item[2:]
            cleaned_data.append(item)

        return title_lists, cleaned_data

    except FileNotFoundError:
        logger.error(f"File not found: {html_path}")
        raise
    except UnicodeDecodeError:
        logger.error(f"Encoding error in file: {html_path}")
        raise


def block_list_to_dict(
    title_lists: List[List[str]], data_lists: List[List[str]], is_debug: bool = False
) -> Dict[str, List]:
    """
    将 block 模式的标题和数据转换为字典

    :param title_lists: 标题列表
    :param data_lists: 数据列表
    :param is_debug: 是否打印调试信息
    :return: 性能数据字典
    """
    # 处理未完成的 rd
    if len(title_lists) - len(data_lists) == 1:
        title_lists.pop()

    # 提取时间列和 rate 列
    start_time_list = [item[0] for item in data_lists]
    rate_list = [item[3] for item in title_lists]

    # 解析标题为字典
    temp_list1 = [sublist[1:] for sublist in title_lists]
    temp_list2 = [item[:1] + item[3:] for item in temp_list1]
    title_dicts = [
        dict(item.split("=") for item in sublist if "=" in item)
        for sublist in temp_list2
    ]

    # 构建数据字典
    data_dict: Dict[str, List] = {
        "start time": start_time_list,
        "rd name": [d.get("RD") for d in title_dicts],
        "rate": rate_list,
        "elapsed": [_safe_int(d.get("elapsed")) for d in title_dicts],
        "warmup": [_safe_int(d.get("warmup")) for d in title_dicts],
        "rdpct": [_safe_int(d.get("rdpct")) for d in title_dicts],
        "xfersize": [d.get("xfersize") for d in title_dicts],
        "threads": [d.get("threads") for d in title_dicts],
    }

    # 添加性能数据列
    no_time_lists = [sublist[1:] for sublist in data_lists]
    for col_name, col_idx in BLOCK_PERF_COLUMNS.items():
        data_dict[col_name] = [_safe_float(item[col_idx]) for item in no_time_lists]

    if is_debug:
        logger.debug(f"Block data dict: {data_dict}")

    return data_dict


# ==================== 辅助函数 ====================


def _safe_int(value: Any) -> Optional[int]:
    """安全转换为 int"""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _safe_float(value: Any) -> Optional[float]:
    """安全转换为 float"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def write_excel(data_dict: Dict[str, List], path: str) -> None:
    """
    将数据字典写入 Excel 文件

    :param data_dict: 数据字典
    :param path: 输出文件路径
    """
    try:
        df = pd.DataFrame(data_dict)
        df.to_excel(path, index=False)
        logger.info(f"Excel file written: {path}")
    except Exception as e:
        logger.error(f"Error writing Excel file: {e}")
        raise


# ==================== License 相关函数 ====================


def license_check() -> None:
    """检查 License 授权"""
    license_dic = parse_license_file()
    try:
        sign = decrypt(license_dic["Sign"])
        sign_list = sign.split("#")
        uuid = sign_list[0].strip()
        date = sign_list[1].strip()
    except Exception as e:
        logger.error("The license's sign is invalid.")
        logger.error(str(e))
        sys.exit(1)

    if (uuid != license_dic["UUID"]) or (date != license_dic["Date"]):
        logger.error("License file is modified!")
        sys.exit(1)

    if len(sign_list) == 2:
        uuid = get_sys_uuid()
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        if sign_list[0] != uuid:
            pass  # UUID 检查已禁用
        if sign_list[1] < current_date:
            logger.error("License is expired!")
            logger.error("Please check your license in /opt/parse_totals/License.dat")
            sys.exit(1)
    else:
        logger.error("Wrong Sign setting on license file.")
        sys.exit(1)


def parse_license_file() -> Dict[str, str]:
    """解析 License 文件"""
    base_path = os.path.normpath(LICENSE_DIR)

    if not os.path.exists(base_path):
        try:
            os.makedirs(base_path)
            logger.info(f"Directory created: {base_path}")
        except OSError as e:
            logger.error(f"Error creating directory: {e}")

    try:
        license_dic = {}
        with open(LICENSE_FILE, "r") as LF:
            for line in LF:
                match = re.match(r"^\s*(\S+)\s*:\s*(\S+)\s*$", line)
                if match:
                    license_dic[match.group(1)] = match.group(2)
        return license_dic
    except FileNotFoundError:
        logger.error(f"ERROR: License file '{LICENSE_FILE}' not found.")
        sys.exit(1)


def decrypt(content: str) -> str:
    """AES 解密"""
    aes = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    decrypted_content = aes.decrypt(a2b_hex(content.encode("utf-8")))
    return decrypted_content.decode("utf-8")  # type: ignore[no-any-return]


def get_sys_uuid() -> str:
    """获取系统 UUID"""
    try:
        result = subprocess.run(
            ["/sbin/dmidecode", "-s", "system-uuid"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip().split("\n")[0] if result.stdout else ""
    except Exception:
        return ""


# ==================== 路径处理函数 ====================


def create_random_file(path: str) -> str:
    """
    如果文件名称已经存在，则在文件名后面添加时间戳

    :param path: 原路径
    :return: 新路径
    """
    exist_dir = "/".join(path.split("/")[:-1])
    exist_file_name = path.split("/")[-1]
    time_stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    new_path = os.path.join(
        exist_dir + "/" + exist_file_name[:-5] + "_" + time_stamp + ".xlsx"
    )
    return new_path


def return_filepath(filepath: str, filename: str) -> str:
    """
    返回一个保存 xlsx 文件的路径

    :param filepath: 输入路径
    :param filename: 文件名
    :return: 输出路径
    """
    filepath = os.path.abspath(filepath).replace("\\\\", "/")

    if os.path.isfile(filepath):
        if ".xlsx" in os.path.splitext(filepath)[-1]:
            return filepath
        return os.path.abspath(filepath + ".xlsx").replace("\\\\", "/")

    if os.path.isdir(filepath):
        return os.path.abspath(filepath + "/" + f"{filename}.xlsx").replace("\\\\", "/")

    # 路径不存在
    if ".xlsx" in os.path.splitext(filepath)[-1]:
        new_dir = "/".join(filepath.split("/")[:-1])
        new_file = filepath.split("/")[-1]
        if os.path.exists(new_dir):
            return os.path.abspath(new_dir + "/" + new_file).replace("\\\\", "/")
        os.mkdir(new_dir)
        logger.info(f"Directory created: {new_dir}")
        return os.path.abspath(new_dir + "/" + new_file).replace("\\\\", "/")

    os.mkdir(filepath)
    logger.info(f"Directory created: {filepath}")
    return os.path.abspath(filepath + "/" + f"{filename}.xlsx").replace("\\\\", "/")


def detect_file_type(input_file: str) -> str:
    """
    检测 totals.html 文件类型（file 或 block）

    :param input_file: 输入文件路径
    :return: 'file' 或 'block'
    """
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
        if len(lines) > 4:
            line_5 = lines[4]
            if "<A" in line_5 and "format" in line_5:
                return "file"
    return "block"


def find_totals_files(pattern: str) -> List[str]:
    """
    根据通配符模式查找所有 totals.html 文件

    :param pattern: 文件模式，如 'dir*/totals.html'
    :return: 匹配的文件路径列表
    """
    if not os.path.isabs(pattern):
        pattern = os.path.abspath(pattern)

    files = glob.glob(pattern, recursive=True)
    totals_files = [
        f for f in files if os.path.isfile(f) and os.path.basename(f) == "totals.html"
    ]
    return sorted(totals_files)


def find_totals_in_dir(dir_path: str) -> List[str]:
    """
    在指定目录及其子目录下查找所有 totals.html 文件

    :param dir_path: 目录路径
    :return: 匹配的文件路径列表
    """
    if not os.path.isabs(dir_path):
        dir_path = os.path.abspath(dir_path)

    pattern = os.path.join(dir_path, "**", "totals.html")
    files = glob.glob(pattern, recursive=True)
    totals_files = [f for f in files if os.path.isfile(f)]
    return sorted(totals_files)


# ==================== 主处理逻辑 ====================


def process_single_file(
    input_file: str, output_path: str, is_debug: bool = False
) -> Tuple[bool, str]:
    """
    处理单个 totals.html 文件

    :param input_file: 输入文件路径
    :param output_path: 输出文件路径
    :param is_debug: 是否启用调试模式
    :return: (成功标志，消息)
    """
    try:
        file_type = detect_file_type(input_file)

        if file_type == "file":
            file_lists = parse_file_totals(input_file)
            file_perf_dict = file_list_to_dict(
                file_lists[0], file_lists[1], is_debug=is_debug
            )
            write_excel(file_perf_dict, path=output_path)
        else:
            block_lists = parse_block_totals(input_file)
            block_perf_dict = block_list_to_dict(
                block_lists[0], block_lists[1], is_debug=is_debug
            )
            write_excel(block_perf_dict, path=output_path)

        return True, f"Success: {output_path}"
    except Exception as e:
        logger.error(f"Error processing {input_file}: {e}")
        return False, f"Error processing {input_file}: {e}"


def get_output_path(input_file: str, output_path_arg: Optional[str]) -> str:
    """
    确定输出文件路径

    :param input_file: 输入文件路径
    :param output_path_arg: 命令行输出路径参数
    :return: 输出文件路径
    """
    if output_path_arg is None:
        input_dir = os.path.dirname(input_file)
        dir_name = input_file.split("/")[-2]
        return os.path.join(input_dir, f"{dir_name}.xlsx").replace("\\\\", "/")

    file_name = input_file.split("/")[-2]
    output_path = return_filepath(output_path_arg, file_name)

    if os.path.exists(output_path):
        output_path = create_random_file(output_path)

    return output_path


def input_args() -> Tuple[argparse.Namespace, List[str]]:
    """
    处理输入的参数

    :return: (args, unknown_args)
    """
    arg_parse = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    arg_parse.add_argument(
        "-v", "--version", action="version", version=VERSION, help="Show version"
    )
    arg_parse.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode.\nExample: parse_totals_v2 -f <totals.html> --debug",
    )
    arg_parse.add_argument(
        "-C", "--output_path", help="The path can be dir or file."
    )
    arg_parse.add_argument(
        "-f",
        "--totals_file",
        help="Specify the totals.html file, directory, or pattern.\n"
        "  - File: parse_totals_v2 -f /path/to/totals.html\n"
        "  - Dir:  parse_totals_v2 -f /path/to/dir/\n"
        "  - Pattern: parse_totals_v2 -f 'dir*/totals.html'",
    )
    arg_parse.add_argument(
        "--batch",
        action="store_true",
        help="Enable batch mode for processing multiple directories.\nExample: parse_totals_v2 -f 'dir*/totals.html' --batch",
    )
    arg_parse.add_argument(
        "paths",
        nargs="*",
        help="Path(s) to process (file, directory, or pattern). Supports multiple paths for batch mode.",
    )
    arg_parse.add_argument("--example", help="parse_totals_v2 -f <totals.html>")

    args, un_args = arg_parse.parse_known_args()

    # 合并 -f 参数和位置参数
    if args.paths:
        if args.totals_file:
            args.totals_file = args.totals_file + " " + " ".join(args.paths)
        else:
            args.totals_file = " ".join(args.paths)

    if len(sys.argv) == 1:
        arg_parse.print_help()
        sys.exit(0)

    return args, un_args


def collect_totals_files(input_patterns: List[str], batch_mode: bool) -> Tuple[List[str], List[str]]:
    """
    收集所有需要处理的 totals.html 文件

    :param input_patterns: 输入模式列表
    :param batch_mode: 是否批量模式
    :return: (文件路径列表，跳过的路径列表)
    """
    totals_files = []
    skipped = []

    for pattern in input_patterns:
        pattern = pattern.replace("\\\\", "/")

        # 通配符模式
        if "*" in pattern or "?" in pattern or batch_mode:
            files = find_totals_files(pattern)
            totals_files.extend(files)
            if not files:
                dir_pattern = pattern.rstrip("/") + "/**/totals.html"
                files = find_totals_files(dir_pattern)
                totals_files.extend(files)
        # 目录模式
        elif os.path.isdir(pattern):
            files = find_totals_in_dir(pattern)
            totals_files.extend(files)
        # 文件模式 - 确保是 totals.html 文件
        elif os.path.isfile(pattern):
            if os.path.basename(pattern) == "totals.html":
                totals_files.append(os.path.abspath(pattern))
            else:
                skipped.append(pattern)
        else:
            # 路径不存在
            skipped.append(pattern)

    return sorted(set(totals_files)), skipped


def main() -> None:
    """主函数"""
    # 预检查系统 UUID（不实际使用）
    get_sys_uuid()

    # License 检查（默认禁用）
    # license_check()

    # 解析参数
    known_args, _ = input_args()

    try:
        if known_args.totals_file is None:
            logger.error("The -f parameter is required.")
            sys.exit(1)

        # 收集所有文件
        input_patterns = known_args.totals_file.split()
        totals_files, skipped = collect_totals_files(input_patterns, known_args.batch)

        # 显示跳过的路径
        if skipped:
            logger.info(f"Skipped {len(skipped)} invalid path(s):")
            for s in skipped:
                logger.info(f"  - {s}")

        if not totals_files:
            if len(input_patterns) == 1:
                pattern = input_patterns[0]
                if os.path.isdir(pattern):
                    logger.error(f"No totals.html files found in directory: '{pattern}'")
                else:
                    logger.error(f"No totals.html files found matching pattern: '{pattern}'")
            else:
                logger.error("No totals.html files found matching the given patterns")
            sys.exit(1)

        # 批量处理
        logger.info(f"Found {len(totals_files)} totals.html file(s):")
        for f in totals_files:
            logger.info(f"  - {f}")

        results = []
        for i, input_file in enumerate(totals_files, 1):
            logger.info(f"[{i}/{len(totals_files)}] Processing: {input_file}...")
            output_path = get_output_path(input_file, known_args.output_path)
            success, msg = process_single_file(input_file, output_path, known_args.debug)
            results.append((input_file, success, msg))
            logger.info("Done" if success else "Failed")

        # 汇总报告
        logger.info("=" * 60)
        logger.info("BATCH PROCESSING SUMMARY")
        logger.info("=" * 60)
        success_count = sum(1 for _, success, _ in results if success)
        fail_count = len(results) - success_count
        logger.info(f"Total: {len(results)} | Success: {success_count} | Failed: {fail_count}")

        if fail_count > 0:
            logger.info("Failed files:")
            for input_file, success, msg in results:
                if not success:
                    logger.info(f"  - {input_file}: {msg}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
