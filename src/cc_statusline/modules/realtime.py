"""实时监控模块。

提供代理状态和任务进度显示。
"""

from typing import Any

from cc_statusline.modules.base import (
    BaseModule,
    ModuleMetadata,
    ModuleOutput,
    ModuleStatus,
)
from cc_statusline.modules.registry import ModuleRegistry


class AgentStatusModule(BaseModule):
    """代理状态模块。

    显示正在执行的子代理和工具状态。
    """

    def __init__(self) -> None:
        self._active_agents: list[dict[str, Any]] = []
        self._active_tools: list[dict[str, Any]] = []
        self._context: dict[str, Any] = {}
        self._max_items: int = 2

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="agent_status",
            description="显示子代理执行状态",
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
        self._active_agents = context.get("active_agents", [])
        self._active_tools = context.get("active_tools", [])

    def refresh(self) -> None:
        """刷新代理状态。"""
        self._active_agents = self._context.get("active_agents", [])
        self._active_tools = self._context.get("active_tools", [])

    def _format_agent(self, agent: dict[str, Any]) -> str:
        """格式化代理信息。

        Args:
            agent: 代理信息

        Returns:
            格式化后的字符串
        """
        name = agent.get("name", "Unknown")
        status = agent.get("status", "running")
        elapsed = agent.get("elapsed_seconds", 0)

        if elapsed > 0:
            if elapsed < 60:
                time_str = f"{elapsed}s"
            else:
                time_str = f"{elapsed // 60}m"
            return f"{name}: {time_str}"
        return name

    def _format_tool(self, tool: dict[str, Any]) -> str:
        """格式化工具信息。

        Args:
            tool: 工具信息

        Returns:
            格式化后的字符串
        """
        name = tool.get("name", "Unknown")
        status = tool.get("status", "running")
        elapsed = tool.get("elapsed_seconds", 0)

        if elapsed > 0:
            if elapsed < 60:
                time_str = f"{elapsed}s"
            else:
                time_str = f"{elapsed // 60}m"
            return f"{name}: {time_str}"
        return name

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        items = []

        # 添加代理
        for agent in self._active_agents[: self._max_items]:
            items.append(self._format_agent(agent))

        # 添加工具
        for tool in self._active_tools[: self._max_items - len(items)]:
            items.append(self._format_tool(tool))

        if not items:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        text = " | ".join(items)
        total = len(self._active_agents) + len(self._active_tools)

        return ModuleOutput(
            text=text,
            icon="🛠️",
            color="blue",
            status=ModuleStatus.SUCCESS,
            tooltip=f"活动任务: {total} 个",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return bool(self._active_agents or self._active_tools)

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 2.0  # 2秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class TodoProgressModule(BaseModule):
    """TODO 进度模块。

    显示 TODO 任务进度。
    """

    def __init__(self) -> None:
        self._total: int = 0
        self._completed: int = 0
        self._context: dict[str, Any] = {}

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="todo_progress",
            description="显示 TODO 任务进度",
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
        todo_data = context.get("todo", {})
        self._total = todo_data.get("total", 0)
        self._completed = todo_data.get("completed", 0)

    def refresh(self) -> None:
        """刷新 TODO 进度。"""
        todo_data = self._context.get("todo", {})
        self._total = todo_data.get("total", 0)
        self._completed = todo_data.get("completed", 0)

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if self._total == 0:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        text = f"{self._completed}/{self._total}"

        # 根据完成度选择颜色
        if self._completed >= self._total:
            color = "green"
            status = ModuleStatus.SUCCESS
        elif self._completed / self._total >= 0.5:
            color = "yellow"
            status = ModuleStatus.SUCCESS
        else:
            color = "blue"
            status = ModuleStatus.SUCCESS

        return ModuleOutput(
            text=text,
            icon="✅",
            color=color,
            status=status,
            tooltip=f"TODO 进度: {self._completed}/{self._total}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._total > 0

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 5.0  # 5秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class ActivityIndicatorModule(BaseModule):
    """活动指示器模块。

    显示实时活动指示器。
    """

    def __init__(self) -> None:
        self._context: dict[str, Any] = {}
        self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._frame_index: int = 0

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="activity_indicator",
            description="显示实时活动指示器",
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

    def refresh(self) -> None:
        """刷新指示器。"""
        self._frame_index = (self._frame_index + 1) % len(self._spinner_frames)

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        # 检查是否有活动
        active_agents = self._context.get("active_agents", [])
        active_tools = self._context.get("active_tools", [])

        if not active_agents and not active_tools:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        frame = self._spinner_frames[self._frame_index]

        return ModuleOutput(
            text=frame,
            icon="",
            color="green",
            status=ModuleStatus.SUCCESS,
            tooltip="处理中...",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        active_agents = self._context.get("active_agents", [])
        active_tools = self._context.get("active_tools", [])
        return bool(active_agents or active_tools)

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 0.1  # 100ms 刷新一次，实现动画效果

    def cleanup(self) -> None:
        """清理资源。"""
        pass


# 自动注册模块
def _register_modules() -> None:
    """注册所有实时监控模块。"""
    modules = [
        ("agent_status", AgentStatusModule),
        ("todo_progress", TodoProgressModule),
        ("activity_indicator", ActivityIndicatorModule),
    ]

    for name, module_class in modules:
        if not ModuleRegistry.has_module(name):
            ModuleRegistry.register(name, module_class)
            ModuleRegistry.enable(name)


# 自动注册
_register_modules()
