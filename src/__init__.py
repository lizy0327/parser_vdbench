"""VDBench totals.html 性能分析工具."""

from .parse_totals_v2 import (
    parse_file_totals,
    parse_block_totals,
    file_list_to_dict,
    block_list_to_dict,
    write_excel,
    detect_file_type,
    find_totals_files,
    process_single_file,
)

__version__ = "2.0.5"
__all__ = [
    "parse_file_totals",
    "parse_block_totals",
    "file_list_to_dict",
    "block_list_to_dict",
    "write_excel",
    "detect_file_type",
    "find_totals_files",
    "process_single_file",
]
