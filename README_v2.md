# VDBench 性能分析工具 v2

[![GitHub](https://img.shields.io/github/v/tag/lizy0327/parser_vdbench?label=version)](https://github.com/lizy0327/parser_vdbench)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**v2 重构优化版** - 修复了 v1 的多个 bug，添加了类型注解和更好的错误处理。

解析 VDBench 性能测试结果（totals.html）并导出为 Excel 文件。

## 项目信息

- **GitHub**: https://github.com/lizy0327/parser_vdbench
- **分支**: `v2-refactor`
- **作者**: lizy0327 (lizy0327@gmail.com)
- **当前版本**: 2.0.1 (v2 重构版)
- **Python 版本**: 3.8+

## v2 主要改进

### 修复的 Bug

| 问题 | 描述 | 修复 |
|------|------|------|
| 🔴 文件类型判断错误 | `if "<A" and "format"` 逻辑错误 | 改为正确的 `detect_file_type()` 函数 |
| 🔴 路径转义错误 | `replace("\\\\", "/")` 只匹配 `\\` | 改为 `replace("\\", "/")` |
| 🔴 重复解析参数 | `input_args()` 被调用多次 | 缓存结果只解析一次 |
| 🔴 命令注入风险 | `shell=True` | 改用 `subprocess.run()` |
| 🔴 大文件内存溢出 | `readlines()` 一次性加载 | 改为逐行迭代 |

### 代码质量改进

| 改进 | 描述 |
|------|------|
| ✅ 类型注解 | 所有函数添加 `-> List`, `-> Dict` 等 |
| ✅ 错误处理 | 添加 `try/except` 捕获异常 |
| ✅ 代码清理 | 删除冗余赋值和废弃代码 |
| ✅ 函数重构 | `__main__` 块抽取为 `main()` 函数 |
| ✅ 正则优化 | `is_time_format` 用正则简化 |
| ✅ 安全移除 | 用列表推导式替代多次 `remove()` |

## 快速开始

### 方法一：直接运行 Python 脚本

```bash
python3 parse_totals_v2.py -f <totals.html 路径>
```

### 方法二：打包为可执行文件

```bash
# 1. 运行打包脚本
bash build_v2.sh

# 2. 安装到系统命令
bash install_command.sh

# 3.  anywhere 运行
parse_totals2 -f <totals.html 路径>
```

## 使用方法

### 解析 totals.html

```bash
# 基本用法
parse_totals2 -f <totals.html 路径>

# 指定输出路径
parse_totals2 -f <totals.html 路径> -C <输出目录或文件路径>

# 调试模式
parse_totals2 -f <totals.html 路径> --debug
```

### 生成 License

```bash
# 获取系统 UUID
python3 gen_license.py -u

# 生成 License 文件
python3 gen_license.py <uuid> <日期>
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `-f`, `--totals_file` | 指定要解析的 totals.html 文件（必需） |
| `-C`, `--output_path` | 输出路径（可以是目录或文件名） |
| `--debug` | 启用调试模式，打印详细数据 |
| `-v`, `--version` | 显示版本号 |

## 输出字段

### File 类型输出

| 字段 | 说明 | 字段 | 说明 |
|------|------|------|------|
| start time | 开始时间 | rd name | RD 名称 |
| elapsed | 运行时长 | warmup | Warmup 时长 |
| rate | 速率 | rdpct | 读百分比 |
| xfersize | 传输大小 | threads | 线程数 |
| iops | IOPS | resp | 响应时间 |
| read mbps | 读吞吐量 | write mbps | 写吞吐量 |
| total mbps | 总吞吐量 | | |

### Block 类型输出

| 字段 | 说明 | 字段 | 说明 |
|------|------|------|------|
| iops | IOPS | mbps | 吞吐量 |
| read pct | 读百分比 | resp time | 响应时间 |
| read resp | 读响应 | resp max | 最大响应 |
| cpu% sys+u | CPU 使用率 | | |

## 与 v1 的区别

| 特性 | v1 (parse_totals) | v2 (parse_totals2) |
|------|-------------------|-------------------|
| 版本 | 4.3.0 | 2.0.0 |
| 文件类型判断 | ❌ 有 bug | ✅ 修复 |
| 路径处理 | ❌ 转义错误 | ✅ 修复 |
| 参数解析 | ❌ 重复调用 | ✅ 缓存结果 |
| 类型注解 | ❌ 无 | ✅ 完整 |
| 错误处理 | ⚠️ 部分 | ✅ 完整 |
| 代码结构 | ⚠️ `__main__` 过大 | ✅ 模块化 |

## 兼容性

- v2 与 v1 完全兼容，可以并行使用
- v2 生成文件名 `parse_totals2`，不影响 v1
- 输入输出格式完全相同

## 部署信息

| 服务器 | IP | 路径 | 用途 |
|--------|-----|------|------|
| c8-vsan | 10.128.58.119 | /home/parse_vdbench/ | 主部署环境 |

## 二进制编译

| 属性 | 值 |
|------|-----|
| 打包工具 | PyInstaller 4.10 |
| 输出位置 | `dist/parse_totals2` |
| 文件大小 | ~40MB |
| 目标平台 | Linux x86_64 |

## 待办事项

- [ ] 添加单元测试
- [ ] 支持并发解析多个文件
- [ ] 添加 CSV 输出格式
- [ ] 支持自定义字段过滤

## Change Log

### 2.0.2 (Bug 修复)

**Bug 修复:**
- 🔴 修复 resp time 列数据错位问题（使用 column_index_map 明确指定每列的原始索引）

### 2.0.1 (输出路径优化)

**优化改进:**
- ✅ 输出文件默认放在 totals.html 同一目录下（无需额外指定 `-C` 参数）
- ✅ Block 类型输出：`resp time` 列移至 `mbps` 列之后，更符合阅读习惯
- ✅ Python 3.6 兼容：`get_sys_uuid()` 使用 `Popen` 替代 `run`

### 2.0.0 (v2 重构版)

**Bug 修复:**
- 修复文件类型判断逻辑错误
- 修复路径转义错误
- 修复参数重复解析
- 修复命令注入风险
- 修复大文件内存问题

**代码改进:**
- 添加完整类型注解
- 添加错误处理
- 删除冗余代码
- 重构 `__main__` 为 `main()` 函数
- 优化 `is_time_format` 用正则

**新功能:**
- `detect_file_type()` 独立函数
- `build_v2.sh` 打包脚本
- `install_command.sh` 系统命令安装

### 1.x (v1 版本)

参见 [README.md](README.md) 的 Change Log

## 相关资源

- [VDBench 官方文档](https://www.oracle.com/downloads/server-storage/vdbench-downloads.html)
- [GitHub 仓库](https://github.com/lizy0327/parser_vdbench)
- [v1 文档](README.md)
