# CLAUDE.md - VDBench 性能分析工具项目指南

## 项目概述

**VDBench 性能分析工具** - 解析 VDBench 性能测试结果（totals.html）并导出为 Excel 文件

| 属性 | 值 |
|------|-----|
| **仓库** | https://github.com/lizy0327/parser_vdbench |
| **当前版本** | 2.0.5 (v2-refactor 分支) |
| **Python 版本** | 3.10+ |
| **作者** | lizy0327 (lizy0327@gmail.com) |
| **部署服务器** | c8-vsan (10.128.58.119) |

## 项目结构

```
parse-totals/
├── src/
│   ├── __init__.py              # 包初始化 + 版本导出
│   └── parse_totals_v2.py       # 主程序 (v2.0.5)
├── tests/
│   ├── __init__.py
│   └── test_main.py             # 单元测试
├── pyproject.toml               # 项目配置和依赖
├── README.md                    # 项目文档
├── .gitignore
└── CLAUDE.md                    # 本文件
```

## 核心功能

1. **File 类型解析** - 解析 VDBench file 类型 totals.html，提取 IOPS、延迟、吞吐量等
2. **Block 类型解析** - 解析 block 类型 totals.html，提取 IOPS、MBPS、CPU 使用率等
3. **Excel 导出** - 自动导出为 .xlsx 格式
4. **批量处理** - 支持多目录/多文件批量处理
5. **无引号通配符** - 支持 `parse_totals2 -f dir*/` 无需引号

## 依赖配置

```toml
# 核心依赖
pandas>=2.0
openpyxl>=3.0
pycryptodome>=3.10

# 开发依赖
pytest>=7.0
pytest-cov>=4.0
black>=23.0
ruff>=0.1.0
mypy>=1.0
```

## 常用命令

### 开发环境
```bash
# 安装依赖
pip install -e .

# 运行测试
pytest tests/ -v --cov=src

# 代码检查
ruff check src/
mypy src/ --ignore-missing-imports

# 格式化
black src/ tests/
```

### 打包部署

> **⚠️ 打包策略：默认在远端服务器上打包，不在本地打包**
> 
> 原因：服务器是生产环境 (CentOS 8)，本地是 macOS，二进制文件不兼容。

```bash
# ✅ 推荐：服务器打包 (CentOS 8)
# 服务器：c8-vsan (10.128.58.119)
# 工作目录：/home/parse_vdbench/
cd /home/parse_vdbench
pyinstaller --name parse_totals2 --onefile --console \
  --hidden-import pandas --hidden-import openpyxl \
  --hidden-import Crypto.Cipher.AES parse_totals_v2.py

# 安装到系统路径
cp dist/parse_totals2 /usr/local/bin/
```

### 使用示例
```bash
# 查看版本
parse_totals2 --version

# 单文件解析
parse_totals2 -f /path/to/totals.html

# 多目录批量处理 (无需引号)
parse_totals2 -f zydisk_st_disk_perf.26060*/

# 指定输出路径
parse_totals2 -f <totals.html> -C /output/dir

# 调试模式
parse_totals2 -f <totals.html> --debug
```

## 代码规范

### 类型注解
- 所有函数必须添加完整类型注解
- 使用 `Optional` 处理可能为空的返回值
- 通过 mypy 严格检查

### 日志系统
- 使用 `logging` 模块替代 `print`
- 格式：`%(asctime)s - %(levelname)s - %(message)s`
- 错误使用 `logger.error()`，信息使用 `logger.info()`

### 常量配置
- 所有魔数、魔串提取为常量
- 集中在文件顶部 `# ==================== 常量配置 ====================` 区域

### 错误处理
- 捕获具体异常类型（`FileNotFoundError`, `UnicodeDecodeError`）
- 避免宽泛的 `except Exception`
- 错误日志记录详细信息

## Git 工作流

### 分支策略
| 分支 | 用途 |
|------|------|
| `v2-refactor` | 主开发分支 (默认) |
| `master` | 旧代码保留 |

### 提交规范
```bash
# 功能新增
git commit -m "feat: 添加 XX 功能"

# Bug 修复
git commit -m "fix: 修复 XX 问题"

# 代码优化
git commit -m "refactor: 优化 XX 代码结构"

# 文档更新
git commit -m "docs: 更新 XX 文档"

# 测试相关
git commit -m "test: 添加 XX 测试用例"
```

### 推送命令
```bash
git add .
git commit -m "描述"
git push origin v2-refactor
```

## 关键代码模块

### 常量配置 (parse_totals_v2.py)
```python
VERSION = "2.0.5"
LICENSE_DIR = "/opt/parse_totals/"
AES_KEY = b"0CoJUm3Qyw3W3jud"
AES_IV = b"0123456789123456"
FILE_PERF_COLUMNS = {...}  # file 模式列索引
BLOCK_PERF_COLUMNS = {...} # block 模式列索引
```

### 核心函数
| 函数 | 作用 |
|------|------|
| `parse_file_totals()` | 解析 file 类型 HTML |
| `parse_block_totals()` | 解析 block 类型 HTML |
| `file_list_to_dict()` | file 数据转字典 |
| `block_list_to_dict()` | block 数据转字典 |
| `collect_totals_files()` | 收集待处理文件 |
| `process_single_file()` | 处理单个文件 |

### 工具函数
| 函数 | 作用 |
|------|------|
| `extract_html_title()` | 提取 HTML 标题 |
| `_safe_int()` | 安全 int 转换 |
| `_safe_float()` | 安全 float 转换 |
| `is_time_format()` | 时间格式检查 |

## License 机制

License 文件位于 `/opt/parse_totals/License.dat`，包含：
- UUID：系统唯一标识
- Date：过期日期
- Sign：加密签名

检查逻辑（默认禁用）：
```python
# license_check()  # 默认注释，不启用
```

## 部署信息

| 服务器 | IP | 路径 | 用途 |
|--------|-----|------|------|
| c8-vsan | 10.128.58.119 | /home/parse_vdbench/ | 主部署环境 |
| 二进制文件 | - | /usr/local/bin/parse_totals2 | 系统命令 |

## 测试用例

```bash
# 运行所有测试
pytest tests/ -v

# 带覆盖率
pytest tests/ -v --cov=src

# 测试文件
tests/test_main.py  # 版本测试
```

## 注意事项

1. **打包大小** - PyInstaller 打包后约 39MB (Linux) / 319MB (macOS)
2. **Python 兼容性** - 服务器 Python 3.6.8，代码需保持向后兼容
3. **License 目录** - 硬编码 `/opt/parse_totals/`，需要 root 权限
4. **UUID 获取** - 依赖 `/sbin/dmidecode`，仅 Linux 可用

## 待办事项

- [ ] 完善 License 检查模块
- [ ] 添加更多单元测试
- [ ] 支持更多输出格式（CSV、JSON）
- [ ] 添加性能数据可视化功能
