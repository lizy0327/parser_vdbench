# VDBench 性能分析工具

[![GitHub](https://img.shields.io/github/v/tag/lizy0327/parser_vdbench?label=version)](https://github.com/lizy0327/parser_vdbench)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

解析 VDBench 性能测试结果（totals.html）并导出为 Excel 文件。

## 项目信息

- **GitHub**: https://github.com/lizy0327/parser_vdbench
- **作者**: lizy0327 (lizy0327@gmail.com)
- **当前版本**: 4.3.0
- **Python 版本**: 3.8+

## 功能

- 解析 VDBench file 类型和 block 类型的 totals.html 文件
- 自动提取性能数据（IOPS、延迟、吞吐量等）
- 导出为 Excel 格式，便于后续分析

## 项目结构

```
vdbench-parser/
├── parse_totals.py      # 主程序 - 解析 totals.html 导出 Excel
├── check_license.py     # License 验证模块
├── gen_license.py       # License 生成工具
├── parse_totals.spec    # PyInstaller 打包配置
├── requirements.txt     # Python 依赖
├── .gitignore          # Git 忽略文件
└── README.md           # 项目文档
```

## 环境配置

### Linux 配置 Python 开发环境

```bash
yum install python38 python38-libs python38-devel python38-pip -y
pip install pyinstaller
pip3 install pycryptodomex
pip3 install pandas
pip3 install openpyxl
```

### 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 解析 totals.html

```bash
# 基本用法
python parse_totals.py -f <totals.html 路径>

# 指定输出路径
python parse_totals.py -f <totals.html 路径> -C <输出目录或文件路径>

# 调试模式
python parse_totals.py -f <totals.html 路径> --debug
```

### 生成 License

```bash
# 获取系统 UUID
python gen_license.py -u

# 生成 License 文件
python gen_license.py <uuid> <日期>
# 例如：python gen_license.py adf44d56-cb0b-104d-5993-986d637e513a 20241231
```

### 打包为可执行文件

```bash
pyinstaller --onefile parse_totals.py
# 输出在 dist/ 目录
# 文件大小约 40MB
```

## 二进制编译

| 属性 | 值 |
|------|-----|
| 打包工具 | PyInstaller 4.10 |
| 输出位置 | `dist/parse_totals` |
| 文件大小 | ~40MB |
| 目标平台 | Linux x86_64 |

### 编译环境
```bash
# 服务器：c8-vsan (10.128.58.119)
# 工作目录：/home/parse_vdbench/
# 二进制位置：/home/parse_vdbench/dist/parse_totals
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `-f`, `--totals_file` | 指定要解析的 totals.html 文件（必需） |
| `-C`, `--output_path` | 输出路径（可以是目录或文件名） |
| `--debug` | 启用调试模式，打印详细数据 |
| `-v`, `--version` | 显示版本号 |

## 输出

程序自动识别测试类型：
- **File 类型**：提取 IOPS、resp、read/write 比率、吞吐量等
- **Block 类型**：提取 IOPS、MBPS、延迟、CPU 使用率等

输出为 `.xlsx` 文件，可直接用 Excel 打开分析。

### 输出字段说明

**File 类型输出字段：**
| 字段 | 说明 | 字段 | 说明 |
|------|------|------|------|
| start time | 开始时间 | rd name | RD 名称 |
| elapsed | 运行时长 | warmup | Warmup 时长 |
| rate | 速率 | rdpct | 读百分比 |
| xfersize | 传输大小 | threads | 线程数 |
| iops | IOPS | resp | 响应时间 |
| read mbps | 读吞吐量 | write mbps | 写吞吐量 |
| total mbps | 总吞吐量 | | |

**Block 类型输出字段：**
| 字段 | 说明 | 字段 | 说明 |
|------|------|------|------|
| iops | IOPS | mbps | 吞吐量 |
| read pct | 读百分比 | resp time | 响应时间 |
| read resp | 读响应 | resp max | 最大响应 |
| cpu% sys+u | CPU 使用率 | | |

## License 使用说明

1. 使用 `gen_license.py` 生成 `License.dat` 文件
2. 生成的 `License.dat` 虽然是明文的，但经过加密处理，如果被编辑过，文件的指纹会变化
3. 主程序在运行时会获取系统的 uuid 和时间信息，和 `License.dat` 内容做对比，如果有任何一项不符合要求，会自动退出程序
4. 为了简化使用成本，检查 uuid 的方法默认设置为 pass，即不检查 uuid

## 部署信息

| 服务器 | IP | 路径 | 用途 |
|--------|-----|------|------|
| c8-vsan | 10.128.58.119 | /home/parse_vdbench/ | 主部署环境 |

## 使用场景

1. **存储性能测试分析** - 解析 VDBench 性能测试结果，导出 Excel 用于报告
2. **批量数据处理** - 支持多次运行结果对比，自动识别不同 RD 配置

## 待办事项

- [ ] `check_license.py` 程序还有待完善
- [ ] 输出路径可以支持文件名

## Change Log

### 4.3.0
- 优化输出文件命名逻辑，支持自定义文件名

### 4.2 (2024/03/26)
- 把 threads 数量类型由 int 变为 string，因为 1024 线程在 vdbench 里会被识别为 1k

### 4.2 (2024/01/03)
- 优化 license 检测和提示

### 4.1 (2023/11/12)
- 优化 license 文件检查机制
- 后续版本号使用 2 位数

### 4.0 (2023/11/12)
1. 优化了 title_list 取值判断规则，把每个 title_list 转换为字典，通过 get 取值，这样参数位置变化就不会影响取值结果了
2. 优化了 block 类型数据分析代码，考虑了时间和 avg 挨着的（17:08:39.047avg_31-330）特殊数据的处理，把时间和 avg 分离
3. 因为第 2 步骤优化了以后，导致所有的 block data list 都是正常的数据，不用在判断第 1 列的数据类型了
4. 优化了字典更新的代码逻辑，使用自定义 title list 和 for 循环来减少代码的臃肿

### 3.1.1 (2023/09/20)
- open license check

### 3.1.0 (2023/09/19)
- fix bug，优化处理文件性能数据时，对于埋数据类型的判断
- 优化文件保存目录处理逻辑，文件输出参数支持目录、文件或目录和文件的组合

### 3.0.2 (2023/09/18)
- fix bug，优化处理文件性能数据时，对于埋数据类型的判断

### 3.0.1 (2023/09/11)
- 处理 datalist 时，第 1 个字段有可能是时间也有可能是 iops 的判断，增加了判断机制

### 3.0
- 新增对块设备结果的解析功能

### 2.0.1
- 修复参数检查 bug

### 2.0 (2023/09/09)
1. 修改 parser_totals 为 parse_totals
2. 优化了文件 input 和 output 路径转换逻辑
3. 重点是进一步熟悉了 argparse 的用法，优化了参数判断，可以指定 -f/-C/--debug 等参数，而且不用人为的判断参数位置和数量

### 1.6 (2023/08/28)
- 添加 license 限制功能

### 1.5.1 (2023/08/27)
- 添加了判断区分 block 和 file 不同类型性能结果的判断逻辑

### 1.5
- 解决如何过滤埋数据 RD 的问题，当然这个也和 vdbench 脚本编写逻辑有关
- 后面版本优化，最理想状态是可以自定义要过滤的 titile 和 data 关键字最好
