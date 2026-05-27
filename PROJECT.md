# VDBench Parser 项目信息

## 基本信息

| 字段 | 值 |
|------|-----|
| 项目名称 | vdbench-parser |
| GitHub 仓库 | https://github.com/lizy0327/parser_vdbench |
| 当前版本 | 4.3.0 |
| 作者 | lizy0327 |
| 邮箱 | lizy0327@gmail.com |
| 创建时间 | 2023-06-20 |
| 最后更新 | 2026-05-27 |
| 语言 | Python 3.8+ |
| 许可证 | MIT |

## 功能概述

VDBench 性能分析工具，用于解析 VDBench 性能测试结果（totals.html）并导出为 Excel 文件。

核心功能：
- 解析 VDBench file 类型的 totals.html 文件
- 解析 VDBench block 类型的 totals.html 文件
- 自动提取性能数据（IOPS、延迟、吞吐量等）
- 导出为 Excel 格式（.xlsx）

## 技术栈

- **Python 3.8+**
- **pandas** - 数据处理和 Excel 导出
- **pycryptodome** - AES 加密/解密（License 验证）
- **openpyxl** - Excel 文件读写
- **PyInstaller** - 打包为可执行文件

## 文件说明

### 核心文件

| 文件 | 说明 | 行数 |
|------|------|------|
| `parse_totals.py` | 主程序，解析 totals.html 并导出 Excel | ~520 行 |
| `check_license.py` | License 验证模块（MAC/UUID + 日期校验） | ~90 行 |
| `gen_license.py` | License 生成工具（AES 加密） | ~80 行 |
| `parse_totals.spec` | PyInstaller 打包配置文件 | ~40 行 |

### 配置文件

| 文件 | 说明 |
|------|------|
| `requirements.txt` | Python 依赖列表 |
| `.gitignore` | Git 忽略文件 |

### 文档文件

| 文件 | 说明 |
|------|------|
| `README.md` | 用户使用文档 |
| `PROJECT.md` | 项目元数据文档 |

## 版本历史

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| 4.3.0 | 2026-05-27 | 优化输出文件命名逻辑，支持自定义文件名 |
| 4.2 | 2024/03/26 | threads 类型改为 string（支持 1k 表示法） |
| 4.2 | 2024/01/03 | 优化 license 检测和提示 |
| 4.1 | 2023/11/12 | 优化 license 检查，版本号改为 2 位数 |
| 4.0 | 2023/11/12 | 优化 title_list 取值、block 数据处理 |
| 3.1.1 | 2023/09/20 | open license check |
| 3.1.0 | 2023/09/19 | 优化文件保存目录处理逻辑 |
| 3.0.2 | 2023/09/18 | 修复埋数据判断 bug |
| 3.0.1 | 2023/09/11 | 增加时间/iops 判断机制 |
| 3.0 | 2023/09/09 | 新增块设备结果解析功能 |
| 2.0 | 2023/09/09 | 优化参数处理逻辑 |
| 1.6 | 2023/08/28 | 添加 license 限制功能 |
| 1.5 | 2023/08/27 | 区分 block 和 file 类型 |

## 依赖环境

```
pandas>=2.0.0
pycryptodome>=3.18.0
openpyxl>=3.1.0
```

## 构建和部署

### 安装依赖
```bash
pip install -r requirements.txt
```

### 打包可执行文件
```bash
pyinstaller --onefile parse_totals.py
# 输出在 dist/parse_totals
# 文件大小约 40MB
```

### 二进制文件信息

| 属性 | 值 |
|------|-----|
| 打包工具 | PyInstaller 4.10 |
| 输出位置 | `dist/parse_totals` |
| 文件大小 | ~40MB |
| 目标平台 | Linux x86_64 |
| Python 版本 | 3.6+ |

### 远程服务器编译环境

```bash
# 服务器：c8-vsan (10.128.58.119)
# 目录：/home/parse_vdbench/

# 已编译二进制位置
/home/parse_vdbench/dist/parse_totals

# 构建目录
/home/parse_vdbench/build/parse_totals/
```

### 系统要求
- Linux (CentOS/RHEL/Ubuntu 等)
- Python 3.8+
- 需要访问 `/sbin/dmidecode`（获取系统 UUID）

## 待办事项

- [ ] 完善 `check_license.py` 程序
- [ ] 输出路径支持文件名
- [ ] 自定义过滤 title 和 data 关键字

## 使用情况

### 典型使用场景

1. **存储性能测试分析**
   - 解析 VDBench 生成的 file/block 性能测试结果
   - 自动提取 IOPS、延迟、吞吐量等关键指标
   - 导出 Excel 用于报告和对比分析

2. **批量数据处理**
   - 支持多次运行的结果对比
   - 自动识别不同的 RD（Run Definition）配置
   - 支持 warmup/elapsed 时间分析

### 输出数据格式

**File 类型测试输出：**
| 字段 | 说明 |
|------|------|
| start time | 开始时间 |
| rd name | RD 名称 |
| elapsed | 运行时长 |
| warmup | Warmup 时长 |
| rate | 速率 |
| rdpct | 读百分比 |
| xfersize | 传输大小 |
| threads | 线程数 |
| iops | IOPS |
| resp | 响应时间 |
| read mbps | 读吞吐量 |
| write mbps | 写吞吐量 |
| total mbps | 总吞吐量 |

**Block 类型测试输出：**
| 字段 | 说明 |
|------|------|
| iops | IOPS |
| mbps | 吞吐量 |
| read pct | 读百分比 |
| resp time | 响应时间 |
| read resp | 读响应 |
| resp max | 最大响应 |
| cpu% sys+u | CPU 使用率 |

### 已知部署位置

| 服务器 | IP | 路径 | 用途 |
|--------|-----|------|------|
| c8-vsan | 10.128.58.119 | /home/parse_vdbench/ | 主部署环境 |

## 相关资源

- [VDBench 官方文档](https://www.oracle.com/downloads/server-storage/vdbench-downloads.html)
- [GitHub 仓库](https://github.com/lizy0327/parser_vdbench)
