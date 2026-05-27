#!/bin/bash
# parse_totals_v2 打包脚本

set -e

echo "======================================"
echo "  parse_totals_v2 打包脚本"
echo "======================================"

# 检查 Python 版本
python3 --version

# 安装依赖
echo ""
echo "正在安装依赖..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# 清理旧的构建文件
echo ""
echo "清理旧的构建文件..."
rm -rf build/
rm -rf dist/

# 打包
echo ""
echo "开始打包 parse_totals2..."
pyinstaller parse_totals_v2.spec

# 验证
echo ""
echo "======================================"
echo "  打包完成！"
echo "======================================"
echo "可执行文件位置：dist/parse_totals2"
echo "文件大小：$(ls -lh dist/parse_totals2 | awk '{print $5}')"

# 测试运行
echo ""
echo "测试运行:"
./dist/parse_totals2 --version
