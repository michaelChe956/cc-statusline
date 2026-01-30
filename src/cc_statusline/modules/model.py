"""模型与上下文模块。

提供模型信息、订阅计划和上下文使用率显示。
"""

from typing import Any, Optional

from cc_statusline.modules.base import (
    BaseModule,
    ModuleMetadata,
    ModuleOutput,
    ModuleStatus,
)
from cc_statusline.modules.registry import ModuleRegistry


class ModelModule(BaseModule):
    """模型信息模块。

    显示当前使用的 Claude 模型 (Sonnet/Opus/Haiku)。
    """

    def __init__(self) -> None:
        self._model: str = ""
        self._context: dict[str, Any] = {}

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="model",
            description="显示当前 Claude 模型",
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
        self._model = self._extract_model_name(context)

    def _extract_model_name(self, context: dict[str, Any]) -> str:
        """从上下文中提取模型名称。

        Args:
            context: 上下文数据

        Returns:
            模型名称
        """
        model = context.get("model", "")
        if not model:
            return ""

        # 简化模型名称
        model_lower = model.lower()
        if "sonnet" in model_lower:
            return "Sonnet"
        elif "opus" in model_lower:
            return "Opus"
        elif "haiku" in model_lower:
            return "Haiku"
        elif "claude" in model_lower:
            # 提取版本号
            parts = model.split()
            for part in parts:
                if part[0].isdigit():
                    return f"Claude {part}"
            return "Claude"
        return model

    def refresh(self) -> None:
        """刷新模型信息。"""
        pass  # 从上下文获取，不需要刷新

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if not self._model:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        return ModuleOutput(
            text=self._model,
            icon="🤖",
            color="purple",
            status=ModuleStatus.SUCCESS,
            tooltip=f"当前模型: {self._model}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return bool(self._model)

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 60.0  # 模型不常变化

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class PlanModule(BaseModule):
    """订阅计划模块。

    显示 Claude Code 订阅计划 (Pro/Free)。
    """

    def __init__(self) -> None:
        self._plan: str = ""
        self._context: dict[str, Any] = {}

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="plan",
            description="显示订阅计划",
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
        self._plan = context.get("plan", "")

    def refresh(self) -> None:
        """刷新计划信息。"""
        pass

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if not self._plan:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        # 根据计划类型选择颜色
        plan_lower = self._plan.lower()
        if "pro" in plan_lower:
            color = "gold"
            icon = "⭐"
        elif "free" in plan_lower:
            color = "blue"
            icon = "🆓"
        else:
            color = "dim"
            icon = "📋"

        return ModuleOutput(
            text=self._plan,
            icon=icon,
            color=color,
            status=ModuleStatus.SUCCESS,
            tooltip=f"订阅计划: {self._plan}",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return bool(self._plan)

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 300.0  # 5分钟刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class ContextPercentModule(BaseModule):
    """上下文使用率百分比模块。

    显示上下文使用百分比。
    """

    def __init__(self) -> None:
        self._percentage: int = 0
        self._context: dict[str, Any] = {}
        self._warning_threshold: int = 70
        self._critical_threshold: int = 90

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="context_pct",
            description="显示上下文使用百分比",
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
        self._percentage = self._calculate_percentage(context)

    def _calculate_percentage(self, context: dict[str, Any]) -> int:
        """计算上下文使用百分比。

        Args:
            context: 上下文数据

        Returns:
            使用百分比 (0-100)
        """
        # 尝试从 cost 数据中获取
        cost_data = context.get("cost", {})
        if "context_percentage" in cost_data:
            return int(cost_data["context_percentage"])

        # 或者从 tokens 计算
        tokens_data = context.get("tokens", {})
        used = tokens_data.get("used", 0)
        limit = tokens_data.get("limit", 0)
        if limit > 0:
            return int((used / limit) * 100)

        return 0

    def refresh(self) -> None:
        """刷新上下文使用率。"""
        self._percentage = self._calculate_percentage(self._context)

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if self._percentage == 0:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        # 根据使用率选择颜色
        if self._percentage >= self._critical_threshold:
            color = "red"
            status = ModuleStatus.ERROR
        elif self._percentage >= self._warning_threshold:
            color = "yellow"
            status = ModuleStatus.WARNING
        else:
            color = "green"
            status = ModuleStatus.SUCCESS

        return ModuleOutput(
            text=f"{self._percentage}%",
            icon="🧠",
            color=color,
            status=status,
            tooltip=f"上下文使用: {self._percentage}%",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._percentage > 0

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 5.0  # 5秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        pass


class ContextBarModule(BaseModule):
    """上下文进度条模块。

    使用进度条显示上下文使用率。
    """

    def __init__(self) -> None:
        self._percentage: int = 0
        self._context: dict[str, Any] = {}
        self._bar_width: int = 10
        self._warning_threshold: int = 70
        self._critical_threshold: int = 90

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="context_bar",
            description="显示上下文使用进度条",
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
        self._percentage = self._calculate_percentage(context)

    def _calculate_percentage(self, context: dict[str, Any]) -> int:
        """计算上下文使用百分比。"""
        cost_data = context.get("cost", {})
        if "context_percentage" in cost_data:
            return int(cost_data["context_percentage"])

        tokens_data = context.get("tokens", {})
        used = tokens_data.get("used", 0)
        limit = tokens_data.get("limit", 0)
        if limit > 0:
            return int((used / limit) * 100)

        return 0

    def _render_bar(self, percentage: int) -> str:
        """渲染进度条。

        Args:
            percentage: 百分比 (0-100)

        Returns:
            进度条字符串
        """
        filled = int((percentage / 100) * self._bar_width)
        empty = self._bar_width - filled

        # 使用不同字符表示填充和空白
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {percentage}%"

    def refresh(self) -> None:
        """刷新进度条。"""
        self._percentage = self._calculate_percentage(self._context)

    def get_output(self) -> ModuleOutput:
        """获取模块输出。"""
        if self._percentage == 0:
            return ModuleOutput(
                text="",
                icon="",
                color="",
                status=ModuleStatus.DISABLED,
            )

        # 根据使用率选择颜色
        if self._percentage >= self._critical_threshold:
            color = "red"
            status = ModuleStatus.ERROR
        elif self._percentage >= self._warning_threshold:
            color = "yellow"
            status = ModuleStatus.WARNING
        else:
            color = "green"
            status = ModuleStatus.SUCCESS

        bar_text = self._render_bar(self._percentage)

        return ModuleOutput(
            text=bar_text,
            icon="🧠",
            color=color,
            status=status,
            tooltip=f"上下文使用: {self._percentage}%",
        )

    def is_available(self) -> bool:
        """检查模块是否可用。"""
        return self._percentage > 0

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。"""
        return 5.0

    def cleanup(self) -> None:
        """清理资源。"""
        pass


# 自动注册模块
def _register_modules() -> None:
    """注册所有模型相关模块。"""
    modules = [
        ("model", ModelModule),
        ("plan", PlanModule),
        ("context_pct", ContextPercentModule),
        ("context_bar", ContextBarModule),
    ]

    for name, module_class in modules:
        if not ModuleRegistry.has_module(name):
            ModuleRegistry.register(name, module_class)
            ModuleRegistry.enable(name)


# 自动注册
_register_modules()
