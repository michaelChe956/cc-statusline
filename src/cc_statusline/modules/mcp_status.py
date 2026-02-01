"""MCP 状态模块。

显示所有 MCP 服务器的状态信息。
"""

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from cc_statusline.modules.base import (
    BaseModule,
    ModuleMetadata,
    ModuleOutput,
    ModuleStatus,
)
from cc_statusline.modules.registry import ModuleRegistry


@dataclass
class MCPServerInfo:
    """MCP 服务器信息。"""

    name: str
    status: str  # running, stopped, error
    command: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    error_message: Optional[str] = None


class MCPStatusModule(BaseModule):
    """MCP 状态模块。

    显示所有 MCP 服务器的状态。
    """

    def __init__(self) -> None:
        super().__init__()
        self._servers: dict[str, MCPServerInfo] = {}
        self._all_configured: list[str] = []  # 所有配置的服务器名称
        self._last_update: float = 0.0
        self._cache_timeout: float = 60.0  # 1分钟缓存
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._pending_update: Optional[Future] = None
        self._config_cache: Optional[list[MCPServerInfo]] = None  # 配置缓存
        self._config_cache_time: float = 0.0
        self._config_cache_ttl: float = 30.0  # 配置缓存30秒

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="mcp_status",
            description="显示所有 MCP 服务器状态",
            version="1.0.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        pass

    def refresh(self) -> None:
        """刷新 MCP 服务器状态。"""
        # 首次刷新使用快速模式（避免 --once 模式下耗时过长）
        fast_mode = not self._servers
        self._refresh_servers(fast_mode=fast_mode)

    def _refresh_servers(self, fast_mode: bool = False) -> None:
        """刷新服务器列表。

        Args:
            fast_mode: 是否使用快速模式（跳过耗时命令）
        """
        servers = self._detect_mcp_servers(fast_mode=fast_mode)
        self._servers = {s.name: s for s in servers}
        self._last_update = _get_current_time()

    def _detect_mcp_servers(self, fast_mode: bool = False) -> list[MCPServerInfo]:
        """检测 MCP 服务器。

        Args:
            fast_mode: 是否使用快速模式（跳过耗时命令）

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []

        # 1. 首先从配置文件加载所有配置的服务器
        config_servers = self._get_from_config()
        for server in config_servers:
            if server.name not in self._all_configured:
                self._all_configured.append(server.name)

        # 2. 尝试使用 claude mcp list 命令获取实际运行状态
        command_servers = self._get_from_claude_command(fast_mode=fast_mode)

        # 3. 合并结果
        command_map = {s.name: s for s in command_servers}

        for name in self._all_configured:
            if name in command_map:
                servers.append(command_map[name])
            elif fast_mode:
                # 快速模式：假设配置的服务器都在运行
                servers.append(MCPServerInfo(name=name, status="running"))
            else:
                # 配置中有但命令没返回，标记为 unknown
                servers.append(MCPServerInfo(name=name, status="unknown"))

        return servers

    def _get_from_claude_command(self, fast_mode: bool = False) -> list[MCPServerInfo]:
        """从 claude mcp list 命令获取服务器信息。

        Args:
            fast_mode: 是否使用快速模式（跳过耗时命令，仅从配置推断）

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []

        # 快速模式：跳过耗时的 claude mcp list 命令
        # 适用于 --once 模式或首次加载
        if fast_mode:
            # 假设所有配置的服务器都在运行
            # 这是合理的，因为 MCP 服务器通常由 Claude Code 自动管理
            return servers

        try:
            # 尝试运行 claude mcp list
            # 注意：此命令可能需要 40+ 秒才能完成（需要检查所有 MCP 服务器健康状态）
            result = subprocess.run(
                ["claude", "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=60,  # 增加超时时间到 60 秒
            )

            if result.returncode == 0:
                servers.extend(self._parse_mcp_list_output(result.stdout))
        except subprocess.TimeoutExpired:
            # 命令超时，返回空列表（将在下次重试）
            pass
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return servers

    def _parse_mcp_list_output(self, output: str) -> list[MCPServerInfo]:
        """解析 claude mcp list 命令输出。

        Args:
            output: 命令输出

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()

            # 跳过空行和非服务器行
            if not line or line.startswith("Checking"):
                continue

            # 新格式: "server-name: command - ✓ Connected"
            if " - ✓ Connected" in line:
                # 提取服务器名称（冒号前的部分）
                parts = line.split(":", 1)
                if len(parts) >= 1:
                    name = parts[0].strip()
                    status = "running"  # ✓ Connected 表示正在运行

                    servers.append(
                        MCPServerInfo(
                            name=name,
                            status=status,
                        )
                    )

        return servers

    def _get_from_config(self) -> list[MCPServerInfo]:
        """从配置文件获取服务器信息（带缓存）。

        配置文件结构 (~/.claude.json):
        {
            "mcpServers": { ... },  // 用户级别的 MCP 服务器
            "projects": {
                "/path/to/project1": {
                    "mcpServers": { ... }  // 项目级别的 MCP 服务器
                }
            }
        }

        Returns:
            MCP 服务器列表
        """
        # 检查配置缓存是否有效
        now = _get_current_time()
        if self._config_cache is not None and (now - self._config_cache_time) <= self._config_cache_ttl:
            return self._config_cache

        servers: list[MCPServerInfo] = []

        # 配置文件路径
        config_path = Path.home() / ".claude.json"

        if not config_path.exists():
            self._config_cache = servers
            self._config_cache_time = now
            return servers

        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            # 1. 解析用户级别的 MCP 服务器
            global_servers = config.get("mcpServers", {})
            for name, server_config in global_servers.items():
                command = None
                if isinstance(server_config, dict):
                    command = server_config.get("command")
                    args = server_config.get("args", [])
                    if command:
                        command = f"{command} {' '.join(args)}"

                servers.append(
                    MCPServerInfo(
                        name=name,
                        status="unknown",
                        command=command,
                    )
                )

            # 2. 解析当前项目的 MCP 服务器
            cwd = os.getcwd()
            projects = config.get("projects", {})
            for project_path, project_data in projects.items():
                if cwd.startswith(str(project_path)) or project_path.startswith(cwd):
                    project_servers = project_data.get("mcpServers", {})
                    for name, server_config in project_servers.items():
                        # 避免重复添加
                        if any(s.name == name for s in servers):
                            continue

                        command = None
                        if isinstance(server_config, dict):
                            command = server_config.get("command")
                            args = server_config.get("args", [])
                            if command:
                                command = f"{command} {' '.join(args)}"

                        servers.append(
                            MCPServerInfo(
                                name=name,
                                status="unknown",
                                command=command,
                            )
                        )

        except (json.JSONDecodeError, OSError):
            pass

        # 更新缓存
        self._config_cache = servers
        self._config_cache_time = now
        return servers

    def _parse_mcp_config_for_test(self, config_path: Path) -> list[MCPServerInfo]:
        """解析 MCP 配置文件（仅用于测试）。

        Args:
            config_path: 配置文件路径

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []

        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            # 解析 mcpServers 字段
            mcp_servers = config.get("mcpServers", {})
            for name, server_config in mcp_servers.items():
                command = None
                if isinstance(server_config, dict):
                    command = server_config.get("command")
                    args = server_config.get("args", [])
                    if command:
                        command = f"{command} {' '.join(args)}"

                servers.append(
                    MCPServerInfo(
                        name=name,
                        status="unknown",
                        command=command,
                    )
                )
        except (json.JSONDecodeError, OSError):
            pass

        return servers

    def get_output(self) -> ModuleOutput:
        """获取模块输出。

        策略:
        1. 立即返回配置中的服务器数量
        2. 后台异步获取实际运行状态
        3. 延迟更新状态栏

        Returns:
            模块输出
        """
        # 1. 确保已加载配置
        if not self._all_configured:
            config_servers = self._get_from_config()
            for server in config_servers:
                if server.name not in self._all_configured:
                    self._all_configured.append(server.name)

        total = len(self._all_configured)

        # 2. 启动异步更新（如果尚未启动）
        self._ensure_async_update()

        # 3. 计算运行数量
        running = sum(1 for s in self._servers.values() if s.status == "running")
        errors = sum(1 for s in self._servers.values() if s.status == "error")

        # 4. 确定显示状态
        if total == 0:
            return ModuleOutput(
                text="无 MCP 服务器",
                icon="🔌",
                color="gray",
                status=ModuleStatus.SUCCESS,
            )

        if self._pending_update is not None and not self._pending_update.done():
            # 正在加载中（首次或缓存过期）
            return ModuleOutput(
                text=f"?/{total}",
                icon="🔄",
                color="blue",
                status=ModuleStatus.SUCCESS,
                tooltip="正在检查 MCP 服务器状态...",
            )

        # 命令完成，显示实际状态
        if errors > 0:
            status = ModuleStatus.ERROR
            color = "red"
            icon = "🔴"
            text = f"{errors} 错误"
        elif running < total:
            status = ModuleStatus.WARNING
            color = "yellow"
            icon = "🟡"
            text = f"{running}/{total} 运行中"
        else:
            status = ModuleStatus.SUCCESS
            color = "green"
            icon = "🟢"
            text = f"{running}/{total} 运行中"

        return ModuleOutput(
            text=text,
            icon=icon,
            color=color,
            status=status,
            tooltip=f"MCP 服务器: {', '.join(self._all_configured)}",
        )

    def _ensure_async_update(self) -> None:
        """确保异步更新任务已启动。"""
        if self._pending_update is None or self._pending_update.done():
            # 启动新的异步任务
            self._pending_update = self._executor.submit(self._async_update_status)

    def _async_update_status(self) -> None:
        """异步更新服务器状态。"""
        # 检查缓存是否有效
        if self._servers and _get_current_time() - self._last_update <= self._cache_timeout:
            return

        # 执行 claude mcp list 命令
        command_servers = self._get_from_claude_command()

        # 更新状态
        server_map = {s.name: s for s in command_servers}
        for name in self._all_configured:
            if name in server_map:
                self._servers[name] = server_map[name]
            else:
                # 配置中有但命令没返回，标记为 unknown
                self._servers[name] = MCPServerInfo(name=name, status="unknown")

        self._last_update = _get_current_time()

    def get_server_details(self) -> list[dict[str, Any]]:
        """获取服务器详细信息。

        Returns:
            服务器详情列表
        """
        return [
            {
                "name": name,
                "status": server.status,
                "command": server.command,
                "error": server.error_message,
            }
            for name, server in self._servers.items()
        ]

    def is_available(self) -> bool:
        """检查模块是否可用。

        Returns:
            是否可用
        """
        return True

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。

        Returns:
            刷新间隔（秒）
        """
        return 10.0  # MCP 状态变化不频繁，10秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        self._servers.clear()
        self._all_configured.clear()
        self._config_cache = None
        self._config_cache_time = 0.0
        if self._executor:
            self._executor.shutdown(wait=False)


# 获取当前时间的辅助函数
def _get_current_time() -> float:
    """获取当前时间戳。"""
    import time

    return time.time()


# 注册模块
def _register_module() -> None:
    """注册模块到注册表。"""
    ModuleRegistry.register(
        "mcp_status",
        MCPStatusModule,
    )
    ModuleRegistry.enable("mcp_status")


# 自动注册
_register_module()
