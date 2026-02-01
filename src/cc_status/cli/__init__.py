"""CLI 包初始化。

导出命令行接口相关类型。
"""

from cc_status.cli.commands import create_parser, main

__all__ = [
    "main",
    "create_parser",
]
