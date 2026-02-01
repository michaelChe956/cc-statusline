"""状态栏主引擎。

协调各模块和渲染器，提供统一的状态栏功能。
"""

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from cc_status.engine.scheduler import Scheduler
from cc_status.modules.base import BaseModule, ModuleOutput
from cc_status.modules.registry import ModuleRegistry
from cc_status.theme.loader import ThemeLoader


class DisplayMode(Enum):
    """显示模式枚举。"""

    TERMINAL = "terminal"  # 终端内显示
    STANDALONE = "standalone"  # 独立窗口


@dataclass
class EngineConfig:
    """引擎配置。"""

    theme: str = "modern"
    display_mode: DisplayMode = DisplayMode.TERMINAL
    refresh_interval: float = 1.0
    modules: list[str] = field(default_factory=list)
    enabled: bool = True


class StatuslineEngine:
    """状态栏主引擎。

    管理模块、渲染器和主题，提供状态栏输出。
    """

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        """初始化引擎。

        Args:
            config: 引擎配置
        """
        self._config = config or EngineConfig()
        self._theme_loader = ThemeLoader()
        self._scheduler = Scheduler()
        self._modules: list[BaseModule] = []
        self._outputs: dict[str, ModuleOutput] = {}
        self._state = "stopped"
        self._lock = threading.Lock()
        self._callbacks: dict[str, list[Callable]] = {
            "output_update": [],
            "state_change": [],
            "error": [],
        }
        self._current_theme: Optional[dict[str, Any]] = None
        self._context: dict[str, Any] = {}  # Claude Code 传递的上下文数据

    @property
    def config(self) -> EngineConfig:
        """获取配置。"""
        return self._config

    @property
    def state(self) -> str:
        """获取状态。"""
        return self._state

    def configure(self, **kwargs: Any) -> None:
        """配置引擎。

        Args:
            **kwargs: 配置选项
        """
        if "theme" in kwargs:
            self._config.theme = kwargs["theme"]
        if "display_mode" in kwargs:
            if isinstance(kwargs["display_mode"], str):
                self._config.display_mode = DisplayMode(kwargs["display_mode"])
            else:
                self._config.display_mode = kwargs["display_mode"]
        if "refresh_interval" in kwargs:
            self._config.refresh_interval = max(kwargs["refresh_interval"], 0.1)

    @property
    def context(self) -> dict[str, Any]:
        """获取上下文数据。"""
        return self._context

    def set_context(self, context: dict[str, Any]) -> None:
        """设置上下文数据。

        从 Claude Code statusLine hook 接收的 JSON 数据。

        Args:
            context: 包含 cost.total_duration_ms 等字段的字典
        """
        self._context = context
        # 将上下文传递给所有模块
        for module in self._modules:
            if hasattr(module, "set_context"):
                try:
                    module.set_context(context)
                except Exception:
                    pass

    def load_theme(self, name: Optional[str] = None) -> dict[str, Any]:
        """加载主题。

        Args:
            name: 主题名称（使用配置中的默认主题）

        Returns:
            主题配置
        """
        theme_name = name or self._config.theme
        try:
            self._current_theme = self._theme_loader.load(theme_name)
            return self._current_theme
        except FileNotFoundError:
            # 回退到默认主题
            self._current_theme = self._theme_loader.load("modern")
            return self._current_theme

    def get_theme(self) -> Optional[dict[str, Any]]:
        """获取当前主题。

        Returns:
            主题配置
        """
        return self._current_theme

    def register_module(self, name: str, module_class: type, **kwargs: Any) -> None:
        """注册模块类。

        Args:
            name: 模块名称
            module_class: 模块类
            **kwargs: 模块初始化参数
        """
        ModuleRegistry.register(name, module_class)
        if self._config.modules and name not in self._config.modules:
            self._config.modules.append(name)

    def initialize(self) -> None:
        """初始化引擎。"""
        # 加载主题
        self.load_theme()

        # 获取启用的模块
        if self._config.modules:
            for name in self._config.modules:
                if ModuleRegistry.has_module(name):
                    try:
                        module = ModuleRegistry.get_instance(name)
                        # 如果有上下文数据，先传递给模块
                        # 这样依赖上下文的模块才能正确报告可用性
                        if self._context and hasattr(module, "set_context"):
                            try:
                                module.set_context(self._context)
                            except Exception:
                                pass
                        if module.is_available():
                            self._modules.append(module)
                    except Exception:
                        pass
        else:
            # 使用所有已注册的模块
            self._modules = ModuleRegistry.get_enabled_modules()

        # 设置调度器
        self._scheduler.on_state_change(self._on_scheduler_state_change)
        for module in self._modules:
            interval = module.get_refresh_interval()
            self._scheduler.add_task(
                name=module.metadata.name,
                callback=self._refresh_module(module),
                interval=interval,
            )

    def _refresh_module(self, module: BaseModule) -> Callable[[], None]:
        """创建模块刷新回调。

        Args:
            module: 模块实例

        Returns:
            刷新回调函数
        """

        def refresh() -> None:
            try:
                module.refresh()
                output = module.get_output()
                with self._lock:
                    self._outputs[module.metadata.name] = output
                self._notify_output_update()
            except Exception as e:
                self._notify_error(str(e))

        return refresh

    def start(self) -> None:
        """启动引擎。"""
        if self._state == "running":
            return

        self._state = "running"
        self._notify_state_change()

        # 初始刷新所有模块
        for module in self._modules:
            try:
                module.refresh()
                output = module.get_output()
                self._outputs[module.metadata.name] = output
            except Exception:
                pass

        # 启动调度器
        self._scheduler.start()

    def stop(self) -> None:
        """停止引擎。"""
        if self._state == "stopped":
            return

        self._state = "stopped"
        self._scheduler.stop()

        # 清理所有模块
        for module in self._modules:
            try:
                module.cleanup()
            except Exception:
                pass

        ModuleRegistry.cleanup_all()
        self._outputs.clear()
        self._notify_state_change()

    def pause(self) -> None:
        """暂停引擎。"""
        self._scheduler.pause()
        self._state = "paused"
        self._notify_state_change()

    def resume(self) -> None:
        """恢复引擎。"""
        self._scheduler.resume()
        self._state = "running"
        self._notify_state_change()

    def _on_scheduler_state_change(self, state: str) -> None:
        """调度器状态变化回调。

        Args:
            state: 新状态
        """
        self._notify_state_change()

    def get_outputs(self) -> dict[str, ModuleOutput]:
        """获取所有模块输出。

        Returns:
            模块输出字典
        """
        with self._lock:
            return self._outputs.copy()

    def get_combined_output(self) -> str:
        """获取组合的输出字符串。

        Returns:
            格式化的输出字符串
        """
        outputs = self.get_outputs()
        if not outputs:
            return ""

        if self._current_theme is None:
            self.load_theme()

        separator = (
            self._current_theme.get("icons", {}).get("separator", " │ ")
            if self._current_theme
            else " │ "
        )

        parts = []
        for _name, output in outputs.items():
            if isinstance(output, ModuleOutput):
                text = str(output)
                if text:
                    parts.append(text)

        return separator.join(parts)

    def get_outputs_for_render(self) -> list[ModuleOutput]:
        """获取渲染用的输出列表。

        Returns:
            模块输出列表
        """
        return list(self.get_outputs().values())

    def on_output_update(self, callback: Callable[[], None]) -> None:
        """注册输出更新回调。

        Args:
            callback: 回调函数
        """
        self._callbacks["output_update"].append(callback)

    def on_state_change(self, callback: Callable[[str], None]) -> None:
        """注册状态变化回调。

        Args:
            callback: 回调函数
        """
        self._callbacks["state_change"].append(callback)

    def on_error(self, callback: Callable[[str], None]) -> None:
        """注册错误回调。

        Args:
            callback: 回调函数
        """
        self._callbacks["error"].append(callback)

    def _notify_output_update(self) -> None:
        """通知输出更新。"""
        for callback in self._callbacks["output_update"]:
            try:
                callback()
            except Exception:
                pass

    def _notify_state_change(self) -> None:
        """通知状态变化。"""
        for callback in self._callbacks["state_change"]:
            try:
                callback(self._state)
            except Exception:
                pass

    def _notify_error(self, error: str) -> None:
        """通知错误。

        Args:
            error: 错误信息
        """
        for callback in self._callbacks["error"]:
            try:
                callback(error)
            except Exception:
                pass

    def get_module_info(self) -> list[dict[str, Any]]:
        """获取模块信息。

        Returns:
            模块信息列表
        """
        return [
            {
                "name": m.metadata.name,
                "description": m.metadata.description,
                "enabled": m.metadata.enabled,
                "available": m.is_available(),
                "refresh_interval": m.get_refresh_interval(),
            }
            for m in self._modules
        ]

    def get_theme_info(self) -> dict[str, Any]:
        """获取主题信息。

        Returns:
            主题信息
        """
        if self._current_theme is None:
            self.load_theme()

        return {
            "name": (
                self._current_theme.get("name", "Unknown") if self._current_theme else "Unknown"
            ),
            "description": (
                self._current_theme.get("description", "") if self._current_theme else ""
            ),
            "colors": (
                list(self._current_theme.get("colors", {}).keys()) if self._current_theme else []
            ),
            "icons": (
                list(self._current_theme.get("icons", {}).keys()) if self._current_theme else []
            ),
        }

    def get_status(self) -> dict[str, Any]:
        """获取引擎状态。

        Returns:
            状态信息字典
        """
        return {
            "state": self._state,
            "theme": self._config.theme,
            "display_mode": self._config.display_mode.value,
            "refresh_interval": self._config.refresh_interval,
            "modules": {
                "total": len(self._modules),
                "enabled": sum(1 for m in self._modules if m.is_available()),
            },
            "scheduler": {
                "state": self._scheduler.get_state().value,
                "tasks": self._scheduler.get_task_count(),
            },
        }


# 全局引擎实例
_engine: Optional[StatuslineEngine] = None


def get_engine(config: Optional[EngineConfig] = None) -> StatuslineEngine:
    """获取全局引擎实例。

    Args:
        config: 可选的引擎配置

    Returns:
        引擎实例
    """
    global _engine
    if _engine is None:
        _engine = StatuslineEngine(config)
    return _engine


def reset_engine() -> None:
    """重置全局引擎。"""
    global _engine
    if _engine is not None:
        _engine.stop()
    _engine = None
