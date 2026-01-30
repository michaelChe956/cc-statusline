"""基础信息模块。

提供目录、Git 分支、版本等基础信息。
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from cc_statusline.modules.base import (
    BaseModule,
    ModuleMetadata,
    ModuleOutput,
    ModuleStatus,
)
from cc_statusline.modules.registry import ModuleRegistry


class DirectoryModule(BaseModule):
    """当前目录模块。

    显示当前工作目录，支持路径简写。
    """

    def __init__(self) -> None:
        self._current_dir: str = ""
        self._home_dir: Path = Path.home()
        self._max_depth: int = 2
        self._show_icon: bool = True
        self._home_alias: str = "~"

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="dir",
            description="显示当前目录路径",
            version="1.0.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        pass

    def refresh(self) -> None:
        """刷新目录信息。"""
        cwd = Path.cwd()
        self._current_dir = self._format_path(cwd)

    def _format_path(self, path: Path) -> str:
        """格式化路径。

        Args:
            path: 路径

        Returns:
            格式化后的路径字符串
        """
        try:
            # 尝试转换为相对于 home 的路径
            relative_to_home = path.relative_to(self._home_dir)
            path_str = f"{self._home_alias}/{relative_to_home}"
        except ValueError:
            path_str = str(path)

        # 限制深度
        parts = path_str.split("/")
        if len(parts) > self._max_depth + 1:
            # 显示最后 max_depth 级
            path_str = ".../" + "/".join(parts[-self._max_depth:])

        return path_str

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if not self._current_dir:
            self.refresh()

        return ModuleOutput(
            text=self._current_dir or "unknown",
            icon="📁" if self._show_icon else "",
            color="blue",
            status=ModuleStatus.SUCCESS,
            tooltip=f"当前目录: {Path.cwd()}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return True

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 5.0  # 目录变化不频繁，5秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class GitBranchModule(BaseModule):
    """Git 分支模块。

    显示当前 Git 分支名称。
    """

    def __init__(self) -> None:
        self._branch: str = ""
        self._is_git_repo: bool = False

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="git_branch",
            description="显示当前 Git 分支",
            version="1.0.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        pass

    def refresh(self) -> None:
        """刷新分支信息。"""
        self._branch = self._get_branch()
        self._is_git_repo = bool(self._branch)

    def _get_branch(self) -> str:
        """获取当前 Git 分支。

        Returns:
            分支名称，如果不是 Git 仓库则返回空字符串
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return ""

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if not self._is_git_repo:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        return ModuleOutput(
            text=self._branch,
            icon="🌿",
            color="yellow",
            status=ModuleStatus.SUCCESS,
            tooltip=f"Git 分支: {self._branch}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._is_git_repo

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 3.0  # 3秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class GitStatusModule(BaseModule):
    """Git 状态模块。

    显示当前 Git 仓库状态（干净/脏/冲突）。
    """

    def __init__(self) -> None:
        self._status: str = "clean"
        self._is_git_repo: bool = False
        self._ahead: int = 0
        self._behind: int = 0
        self._symbols = {
            "clean": "✓",
            "dirty": "✗",
            "conflict": "⚠",
        }

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="git_status",
            description="显示 Git 仓库状态",
            version="1.0.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        pass

    def refresh(self) -> None:
        """刷新 Git 状态。"""
        self._status = self._get_status()
        self._is_git_repo = self._status != "unknown"
        if self._is_git_repo:
            self._ahead, self._behind = self._get_ahead_behind()

    def _get_status(self) -> str:
        """获取 Git 状态。

        Returns:
            状态字符串: clean, dirty, conflict, unknown
        """
        try:
            # 检查是否有冲突
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if result.returncode == 0 and result.stdout.strip():
                return "conflict"

            # 检查是否有未提交的更改
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if result.returncode == 0:
                if result.stdout.strip():
                    return "dirty"
                return "clean"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return "unknown"

    def _get_ahead_behind(self) -> tuple[int, int]:
        """获取与远程的 ahead/behind 数量。

        Returns:
            (ahead, behind) 元组
        """
        try:
            result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) == 2:
                    return int(parts[0]), int(parts[1])
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            pass
        return 0, 0

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if not self._is_git_repo:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        # 构建显示文本
        parts = []
        if self._status == "clean":
            parts.append(self._symbols["clean"])
            color = "green"
            status = ModuleStatus.SUCCESS
        elif self._status == "dirty":
            parts.append(self._symbols["dirty"])
            color = "yellow"
            status = ModuleStatus.WARNING
        else:  # conflict
            parts.append(self._symbols["conflict"])
            color = "red"
            status = ModuleStatus.ERROR

        # 添加 ahead/behind 信息
        if self._ahead > 0:
            parts.append(f"↑{self._ahead}")
        if self._behind > 0:
            parts.append(f"↓{self._behind}")

        return ModuleOutput(
            text=" ".join(parts),
            icon="",
            color=color,
            status=status,
            tooltip=f"Git 状态: {self._status}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._is_git_repo

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 3.0

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class VersionModule(BaseModule):
    """Claude Code 版本模块。

    显示 Claude Code 版本信息。
    """

    def __init__(self) -> None:
        self._version: str = ""
        self._context: dict[str, Any] = {}

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="version",
            description="显示 Claude Code 版本",
            version="1.0.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        pass

    def set_context(self, context: dict[str, Any]) -> None:
        """设置上下文数据。"""
        self._context = context
        self._version = context.get("version", "")

    def refresh(self) -> None:
        """刷新版本信息。"""
        # 版本信息从上下文获取，不需要刷新
        pass

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if not self._version:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        return ModuleOutput(
            text=self._version,
            icon="📦",
            color="dim",
            status=ModuleStatus.SUCCESS,
            tooltip=f"Claude Code 版本: {self._version}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return bool(self._version)

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 60.0  # 版本信息不常变化

    def cleanup(self) -> None:
        """清理资源。"""
        pass


# 自动注册模块
def _register_modules() -> None:
    """注册所有基础模块。"""
    modules = [
        ("dir", DirectoryModule),
        ("git_branch", GitBranchModule),
        ("git_status", GitStatusModule),
        ("version", VersionModule),
    ]

    for name, module_class in modules:
        if not ModuleRegistry.has_module(name):
            ModuleRegistry.register(name, module_class)
            ModuleRegistry.enable(name)


# 自动注册
_register_modules()
