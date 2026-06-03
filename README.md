# VDBench Parse Totals

VDBench 性能分析工具 - 解析 VDBench 生成的 `totals.html` 文件并输出 Excel 格式性能报告。

## 功能特性

- **自动识别文件类型**: 支持 file 和 block 两种 VDBench 测试类型
- **性能指标提取**: IOPS、吞吐量、延迟、读写比例、CPU 使用率等
- **Excel 输出**: 使用 pandas 生成结构化的 `.xlsx` 报告
- **命令行工具**: 简单易用的 CLI 接口
- **批量处理**: 支持通配符批量处理多个目录的 totals.html 文件

## 安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"
```

## 使用方法

### 命令行

#### 单文件处理

```bash
# 基本用法
python -m src.parse_totals_v2 -f <totals.html>

# 指定输出路径
python -m src.parse_totals_v2 -f <totals.html> -C /path/to/output.xlsx

# 调试模式
python -m src.parse_totals_v2 -f <totals.html> --debug

# 查看帮助
python -m src.parse_totals_v2 -h
```

#### 批量处理（新功能）

```bash
# 处理当前目录下所有子目录的 totals.html
python -m src.parse_totals_v2 -f 'dir*/totals.html'

# 处理指定路径模式下所有 totals.html
python -m src.parse_totals_v2 -f '/path/to/test*/totals.html'

# 递归查找所有子目录
python -m src.parse_totals_v2 -f '**/totals.html'

# 显式启用批量模式
python -m src.parse_totals_v2 -f 'dir*/totals.html' --batch

# 批量处理并指定输出目录
python -m src.parse_totals_v2 -f 'dir*/totals.html' -C /path/to/output_dir
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-f, --totals_file` | 指定要解析的 totals.html 文件或通配符模式（必需） |
| `-C, --output_path` | 输出路径（目录或文件，可选） |
| `--debug` | 启用调试模式，打印详细数据 |
| `--batch` | 显式启用批量模式（当 -f 包含通配符时自动启用） |
| `-v, --version` | 显示版本号 |

## 输出指标

### File 类型测试
- start time, rd name, elapsed, warmup, rate, rdpct, xfersize, threads
- iops, resp, read pct, read rate, read resp, write rate, write resp
- read mbps, write mbps, total mbps, xfer size

### Block 类型测试
- start time, rd name, rate, elapsed, warmup, rdpct, xfersize, threads
- iops, mbps, resp time, bytes, read pct, read resp, write rate
- resp max, resp stddev, queue depth, cpu% sys+u, cpu% sys

## 开发

```bash
# 运行测试
pytest

# 代码检查
ruff check .
black .
mypy src

# 全部检查
pytest && ruff check . && black --check . && mypy src
```

## 项目结构

```
parse-totals/
├── src/
│   ├── __init__.py
│   └── parse_totals_v2.py    # 主解析逻辑
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── pyproject.toml
├── README.md
└── .gitignore
```

## 版本历史

- **v2.0.1**: 优化重构版 - 类型注解、更好的异常处理、自动文件类型检测
- **v4.3**: 原始版本
