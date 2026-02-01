"""会话时间模块。

跟踪和显示当前会话的使用时间。
从 Claude Code 传递的 total_duration_ms 获取时间。
"""

from datetime import timedelta
from typing import Any, Optional

from cc_status.modules.base import (
    BaseModule,
    ModuleMetadata,
    ModuleOutput,
    ModuleStatus,
)


class SessionTimeModule(BaseModule):
    """会话时间模块。

    显示 Claude Code 会话的运行时长。
    从 Claude Code 传递的 total_duration_ms 获取时间。
    """

    def __init__(self) -> None:
        self._last_elapsed: Optional[timedelta] = None
        self._total_duration_ms: Optional[int] = None  # 来自 Claude Code 的总时长（毫秒）

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="session_time",
            description="显示当前会话使用时间",
            version="1.2.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        pass

    def set_context(self, context: dict[str, Any]) -> None:
        """设置上下文数据。

        从 Claude Code statusLine hook 接收的 JSON 数据。

        Args:
            context: 包含 cost.total_duration_ms 等字段的字典
        """
        self._context = context
        # 提取 total_duration_ms（毫秒）
        cost_data = context.get("cost", {})
        self._total_duration_ms = cost_data.get("total_duration_ms")

    def refresh(self) -> None:
        """刷新时间数据。"""
        self._calculate_elapsed()

    def _calculate_elapsed(self) -> Optional[timedelta]:
        """计算经过的时间。

        使用 Claude Code 传递的 total_duration_ms。

        Returns:
            经过的时间
        """
        if self._total_duration_ms is not None:
            self._last_elapsed = timedelta(milliseconds=self._total_duration_ms)
            return self._last_elapsed
        return None

    def _format_elapsed(self, elapsed: timedelta) -> str:
        """格式化经过的时间。

        Args:
            elapsed: 经过的时间

        Returns:
            格式化后的时间字符串
        """
        total_seconds = int(elapsed.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{total_seconds}s"

    def get_elapsed(self) -> Optional[timedelta]:
        """获取经过的时间。

        Returns:
            经过的时间
        """
        return self._last_elapsed

    def reset(self) -> None:
        """重置会话计时。"""
        self._last_elapsed = None
        self._total_duration_ms = None

    def get_output(self) -> ModuleOutput:
        """获取模块输出。

        Returns:
            模块输出
        """
        elapsed = self._calculate_elapsed()

        if elapsed is None:
            return ModuleOutput(
                text="--:--",
                icon="⏱️",
                color="gray",
                status=ModuleStatus.SUCCESS,
            )

        formatted = self._format_elapsed(elapsed)

        # 根据时长选择颜色
        hours = elapsed.total_seconds() / 3600
        if hours >= 2:
            color = "green"
        elif hours >= 1:
            color = "yellow"
        else:
            color = "blue"

        return ModuleOutput(
            text=formatted,
            icon="⏱️",
            color=color,
            status=ModuleStatus.SUCCESS,
            tooltip=f"会话时长: {formatted}",
        )

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
        return 1.0  # 每秒更新

    def cleanup(self) -> None:
        """清理资源。"""
        pass


# 自动注册（仅在直接运行时执行，测试时会通过 conftest.py 处理）
def _register_module() -> None:
    """注册模块到注册表。"""
    from cc_status.modules.registry import ModuleRegistry

    # 检查是否已注册，避免重复注册
    if not ModuleRegistry.has_module("session_time"):
        ModuleRegistry.register(
            "session_time",
            SessionTimeModule,
        )
        ModuleRegistry.enable("session_time")


# 自动注册
_register_module()
