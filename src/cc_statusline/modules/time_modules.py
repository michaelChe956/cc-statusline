"""时间与计费模块。

提供重置倒计时和计费窗口使用显示。
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from cc_statusline.modules.base import (
    BaseModule,
    ModuleMetadata,
    ModuleOutput,
    ModuleStatus,
)
from cc_statusline.modules.registry import ModuleRegistry


class ResetTimerModule(BaseModule):
    """重置倒计时模块。

    显示到下次重置（通常是每日）的倒计时。
    """

    def __init__(self) -> None:
        self._reset_time: Optional[datetime] = None
        self._context: dict[str, Any] = {}

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="reset_timer",
            description="显示下次重置倒计时",
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
        self._reset_time = self._extract_reset_time(context)

    def _extract_reset_time(self, context: dict[str, Any]) -> Optional[datetime]:
        """从上下文中提取重置时间。

        Args:
            context: 上下文数据

        Returns:
            重置时间，如果没有则返回 None
        """
        # 尝试从 cost 数据中获取
        cost_data = context.get("cost", {})
        reset_timestamp = cost_data.get("next_reset_time")
        if reset_timestamp:
            try:
                # 假设是 Unix 时间戳（秒）
                return datetime.fromtimestamp(reset_timestamp)
            except (ValueError, TypeError):
                pass

        # 如果没有提供，假设是当天午夜
        now = datetime.now()
        next_midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
        return next_midnight

    def _calculate_remaining(self) -> Optional[timedelta]:
        """计算剩余时间。

        Returns:
            剩余时间，如果重置时间未知则返回 None
        """
        if self._reset_time is None:
            return None
        remaining = self._reset_time - datetime.now()
        if remaining.total_seconds() < 0:
            return timedelta(0)
        return remaining

    def _format_duration(self, duration: timedelta) -> str:
        """格式化持续时间。

        Args:
            duration: 持续时间

        Returns:
            格式化后的字符串
        """
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def refresh(self) -> None:
        """刷新倒计时。"""
        # 重置时间从上下文获取，不需要刷新
        pass

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        remaining = self._calculate_remaining()
        if remaining is None:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        formatted = self._format_duration(remaining)

        # 根据剩余时间选择颜色
        total_seconds = remaining.total_seconds()
        if total_seconds < 300:  # 5分钟
            color = "red"
            status = ModuleStatus.WARNING
        elif total_seconds < 1800:  # 30分钟
            color = "yellow"
            status = ModuleStatus.SUCCESS
        else:
            color = "green"
            status = ModuleStatus.SUCCESS

        return ModuleOutput(
            text=formatted,
            icon="🔄",
            color=color,
            status=status,
            tooltip=f"下次重置: {formatted}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._reset_time is not None

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 60.0  # 1分钟刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class BlockUsageModule(BaseModule):
    """计费窗口使用模块。

    显示5小时计费窗口的使用情况。
    """

    def __init__(self) -> None:
        self._block_start: Optional[datetime] = None
        self._block_duration_hours: int = 5
        self._context: dict[str, Any] = {}

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="block_usage",
            description="显示5小时计费窗口使用",
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
        cost_data = context.get("cost", {})
        block_start = cost_data.get("block_start_time")
        if block_start:
            try:
                self._block_start = datetime.fromtimestamp(block_start)
            except (ValueError, TypeError):
                self._block_start = None

    def _calculate_usage(self) -> float:
        """计算计费窗口使用百分比。

        Returns:
            使用百分比 (0-100)
        """
        if self._block_start is None:
            return 0.0

        now = datetime.now()
        elapsed = now - self._block_start
        total_duration = timedelta(hours=self._block_duration_hours)

        if elapsed.total_seconds() < 0:
            return 0.0

        percentage = (elapsed.total_seconds() / total_duration.total_seconds()) * 100
        return min(percentage, 100.0)

    def _render_bar(self, percentage: float) -> str:
        """渲染进度条。

        Args:
            percentage: 百分比 (0-100)

        Returns:
            进度条字符串
        """
        bar_width = 8
        filled = int((percentage / 100) * bar_width)
        empty = bar_width - filled

        bar = "█" * filled + "░" * empty
        return f"[{bar}] {percentage:.0f}%"

    def refresh(self) -> None:
        """刷新使用情况。"""
        pass  # 从上下文获取，不需要刷新

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        usage = self._calculate_usage()
        if usage <= 0 and self._block_start is None:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        formatted = self._render_bar(usage)

        # 根据使用率选择颜色
        if usage >= 90:
            color = "red"
            status = ModuleStatus.WARNING
        elif usage >= 70:
            color = "yellow"
            status = ModuleStatus.SUCCESS
        else:
            color = "green"
            status = ModuleStatus.SUCCESS

        return ModuleOutput(
            text=formatted,
            icon="⏳",
            color=color,
            status=status,
            tooltip=f"计费窗口使用: {usage:.1f}%",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._block_start is not None

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 60.0  # 1分钟刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


# 自动注册模块
def _register_modules() -> None:
    """注册所有时间相关模块。"""
    modules = [
        ("reset_timer", ResetTimerModule),
        ("block_usage", BlockUsageModule),
    ]

    for name, module_class in modules:
        if not ModuleRegistry.has_module(name):
            ModuleRegistry.register(name, module_class)
            ModuleRegistry.enable(name)


# 自动注册
_register_modules()
