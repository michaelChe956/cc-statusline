"""成本统计模块。

提供成本统计和燃烧率计算。
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


class CostSessionModule(BaseModule):
    """会话成本模块。

    显示当前会话的成本。
    """

    def __init__(self) -> None:
        self._cost: float = 0.0
        self._currency: str = "$"
        self._context: dict[str, Any] = {}
        self._decimal_places: int = 2

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="cost_session",
            description="显示当前会话成本",
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
        self._cost = self._extract_cost(context)

    def _extract_cost(self, context: dict[str, Any]) -> float:
        """从上下文中提取成本。

        Args:
            context: 上下文数据

        Returns:
            成本金额
        """
        cost_data = context.get("cost", {})
        # 尝试不同的成本字段（按优先级）
        # Claude Code 传递的是 total_cost_usd
        for key in ["total_cost_usd", "total_cost", "session_cost", "cost", "amount"]:
            if key in cost_data:
                value = cost_data[key]
                if isinstance(value, (int, float)):
                    return float(value)
        return 0.0

    def refresh(self) -> None:
        """刷新成本信息。"""
        self._cost = self._extract_cost(self._context)

    def _format_cost(self, cost: float) -> str:
        """格式化成本金额。

        Args:
            cost: 成本金额

        Returns:
            格式化后的字符串
        """
        return f"{self._currency}{cost:.{self._decimal_places}f}"

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if self._cost <= 0:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        formatted = self._format_cost(self._cost)

        return ModuleOutput(
            text=formatted,
            icon="💰",
            color="green",
            status=ModuleStatus.SUCCESS,
            tooltip=f"当前会话成本: {formatted}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._cost > 0

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 10.0  # 10秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class CostTodayModule(BaseModule):
    """今日成本模块。

    显示今日累计成本。
    """

    def __init__(self) -> None:
        self._session_cost: float = 0.0
        self._today_cost: float = 0.0
        self._currency: str = "$"
        self._context: dict[str, Any] = {}
        self._decimal_places: int = 2

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="cost_today",
            description="显示今日累计成本",
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
        self._session_cost = self._extract_cost(context)
        # 今日成本 = 会话成本 + 历史今日成本（如果有）
        cost_data = context.get("cost", {})
        daily_cost = cost_data.get("daily_cost", 0.0)
        self._today_cost = daily_cost if daily_cost > 0 else self._session_cost

    def _extract_cost(self, context: dict[str, Any]) -> float:
        """从上下文中提取成本。"""
        cost_data = context.get("cost", {})
        # 尝试不同的成本字段（按优先级）
        # Claude Code 传递的是 total_cost_usd
        for key in ["total_cost_usd", "total_cost", "session_cost", "cost"]:
            if key in cost_data:
                value = cost_data[key]
                if isinstance(value, (int, float)):
                    return float(value)
        return 0.0

    def refresh(self) -> None:
        """刷新成本信息。"""
        self._session_cost = self._extract_cost(self._context)

    def _format_cost(self, cost: float) -> str:
        """格式化成本金额。"""
        return f"{self._currency}{cost:.{self._decimal_places}f}"

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        cost = self._today_cost if self._today_cost > 0 else self._session_cost
        if cost <= 0:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        formatted = self._format_cost(cost)

        return ModuleOutput(
            text=formatted,
            icon="📅",
            color="blue",
            status=ModuleStatus.SUCCESS,
            tooltip=f"今日累计成本: {formatted}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return (self._today_cost > 0) or (self._session_cost > 0)

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 60.0  # 1分钟刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class BurnRateModule(BaseModule):
    """燃烧率模块。

    显示每小时成本燃烧率。
    """

    def __init__(self) -> None:
        self._session_cost: float = 0.0
        self._session_duration_ms: int = 0
        self._currency: str = "$"
        self._context: dict[str, Any] = {}
        self._decimal_places: int = 2

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="burn_rate",
            description="显示每小时成本燃烧率",
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
        # 优先使用 total_cost_usd（Claude Code 传递的格式）
        self._session_cost = cost_data.get("total_cost_usd", cost_data.get("total_cost", 0.0))
        self._session_duration_ms = cost_data.get("total_duration_ms", 0)

    def _calculate_burn_rate(self) -> float:
        """计算燃烧率（$/小时）。

        Returns:
            每小时燃烧率
        """
        if self._session_duration_ms <= 0:
            return 0.0

        # 转换为小时
        hours = self._session_duration_ms / (1000 * 60 * 60)
        if hours <= 0:
            return 0.0

        return self._session_cost / hours

    def refresh(self) -> None:
        """刷新燃烧率。"""
        cost_data = self._context.get("cost", {})
        self._session_cost = cost_data.get("total_cost_usd", cost_data.get("total_cost", 0.0))
        self._session_duration_ms = cost_data.get("total_duration_ms", 0)

    def _format_rate(self, rate: float) -> str:
        """格式化燃烧率。"""
        return f"{self._currency}{rate:.{self._decimal_places}f}/h"

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        rate = self._calculate_burn_rate()
        if rate <= 0:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        formatted = self._format_rate(rate)

        # 根据燃烧率选择颜色
        if rate > 5.0:  # $5/小时
            color = "red"
        elif rate > 2.0:  # $2/小时
            color = "yellow"
        else:
            color = "green"

        return ModuleOutput(
            text=formatted,
            icon="🔥",
            color=color,
            status=ModuleStatus.SUCCESS,
            tooltip=f"燃烧率: {formatted}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._calculate_burn_rate() > 0

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 30.0  # 30秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


# 自动注册模块
def _register_modules() -> None:
    """注册所有成本相关模块。"""
    modules = [
        ("cost_session", CostSessionModule),
        ("cost_today", CostTodayModule),
        ("burn_rate", BurnRateModule),
    ]

    for name, module_class in modules:
        if not ModuleRegistry.has_module(name):
            ModuleRegistry.register(name, module_class)
            ModuleRegistry.enable(name)


# 自动注册
_register_modules()
