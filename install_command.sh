#!/bin/bash
# 安装 parse_totals2 到系统命令

set -e

echo "======================================"
echo "  安装 parse_totals2 到系统命令"
echo "======================================"

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    INSTALL_DIR="/usr/local/bin"

    # 检查是否需要 sudo
    if [[ $EUID -ne 0 ]]; then
        echo "需要 sudo 权限，请输入密码..."
        SUDO_CMD="sudo"
    else
        SUDO_CMD=""
    fi

    # 复制可执行文件
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    $SUDO_CMD cp "$SCRIPT_DIR/dist/parse_totals2" "$INSTALL_DIR/"
    $SUDO_CMD chmod +x "$INSTALL_DIR/parse_totals2"

    echo ""
    echo "安装完成！"
    echo "现在可以在任何位置运行：parse_totals2"
    echo ""
    echo "验证安装:"
    parse_totals2 --version

elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    INSTALL_DIR="/usr/local/bin"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cp "$SCRIPT_DIR/dist/parse_totals2" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/parse_totals2"

    echo ""
    echo "安装完成！"
    echo "现在可以在任何位置运行：parse_totals2"
    echo ""
    echo "验证安装:"
    parse_totals2 --version
else
    echo "不支持的操作系统：$OSTYPE"
    exit 1
fi
