"""模块注册表。

提供模块的注册、查找和管理功能。
"""

from typing import Callable, Optional

from cc_status.modules.base import (
    BaseModule,
    ModuleLoadError,
    ModuleMetadata,
    ModuleNotFoundError,
)


class ModuleRegistry:
    """模块注册表。

    管理所有已注册的模块类及其实例。
    """

    _instance: "ModuleRegistry | None" = None
    _classes: dict[str, type[BaseModule]] = {}
    _instances: dict[str, BaseModule] = {}
    _enabled_modules: list[str] = []
    _factory_functions: dict[str, Callable[[], BaseModule]] = {}

    def __new__(cls) -> "ModuleRegistry":
        """单例模式。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置注册表。"""
        cls._classes.clear()
        cls._instances.clear()
        cls._enabled_modules.clear()
        cls._factory_functions.clear()
        cls._instance = None

    @classmethod
    def register(
        cls,
        name: str,
        module_class: type[BaseModule],
        factory: Optional[Callable[[], BaseModule]] = None,
    ) -> None:
        """注册模块类。

        Args:
            name: 模块名称（唯一标识）
            module_class: 模块类
            factory: 可选的工厂函数，用于创建实例
        """
        if name in cls._classes:
            raise ModuleLoadError(f"模块 '{name}' 已注册")

        cls._classes[name] = module_class
        if factory is not None:
            cls._factory_functions[name] = factory

    @classmethod
    def unregister(cls, name: str) -> None:
        """注销模块。

        Args:
            name: 模块名称
        """
        cls._classes.pop(name, None)
        cls._instances.pop(name, None)
        cls._factory_functions.pop(name, None)
        if name in cls._enabled_modules:
            cls._enabled_modules.remove(name)

    @classmethod
    def get_class(cls, name: str) -> type[BaseModule]:
        """获取模块类。

        Args:
            name: 模块名称

        Returns:
            模块类

        Raises:
            ModuleNotFoundError: 模块未找到
        """
        if name not in cls._classes:
            raise ModuleNotFoundError(f"模块 '{name}' 未找到")
        return cls._classes[name]

    @classmethod
    def get_instance(cls, name: str, force_new: bool = False) -> BaseModule:
        """获取模块实例。

        Args:
            name: 模块名称
            force_new: 是否强制创建新实例

        Returns:
            模块实例

        Raises:
            ModuleNotFoundError: 模块未找到
        """
        if name not in cls._classes:
            raise ModuleNotFoundError(f"模块 '{name}' 未找到")

        if force_new or name not in cls._instances:
            module_class = cls._classes[name]
            instance = module_class()
            instance.initialize()
            cls._instances[name] = instance

        return cls._instances[name]

    @classmethod
    def has_module(cls, name: str) -> bool:
        """检查模块是否已注册。

        Args:
            name: 模块名称

        Returns:
            是否已注册
        """
        return name in cls._classes

    @classmethod
    def list_modules(cls, enabled_only: bool = False) -> list[str]:
        """列出所有已注册的模块。

        Args:
            enabled_only: 只返回已启用的模块

        Returns:
            模块名称列表
        """
        if enabled_only:
            return list(cls._enabled_modules)
        return list(cls._classes.keys())

    @classmethod
    def get_metadata(cls, name: str) -> ModuleMetadata:
        """获取模块元数据。

        Args:
            name: 模块名称

        Returns:
            模块元数据
        """
        instance = cls.get_instance(name)
        return instance.metadata

    @classmethod
    def enable(cls, name: str) -> None:
        """启用模块。

        Args:
            name: 模块名称
        """
        if name in cls._classes and name not in cls._enabled_modules:
            cls._enabled_modules.append(name)

    @classmethod
    def disable(cls, name: str) -> None:
        """禁用模块。

        Args:
            name: 模块名称
        """
        if name in cls._enabled_modules:
            cls._enabled_modules.remove(name)

    @classmethod
    def is_enabled(cls, name: str) -> bool:
        """检查模块是否已启用。

        Args:
            name: 模块名称

        Returns:
            是否已启用
        """
        return name in cls._enabled_modules

    @classmethod
    def get_enabled_modules(cls) -> list[BaseModule]:
        """获取所有已启用的模块实例。

        Returns:
            已启用模块实例列表
        """
        instances = []
        for name in cls._enabled_modules:
            try:
                instance = cls.get_instance(name)
                if instance.is_available():
                    instances.append(instance)
            except ModuleNotFoundError:
                continue
        return instances

    @classmethod
    def get_refresh_interval(cls) -> float:
        """获取所有模块的最小刷新间隔。

        Returns:
            最小刷新间隔（秒）
        """
        intervals = []
        for name in cls._enabled_modules:
            try:
                instance = cls.get_instance(name)
                intervals.append(instance.get_refresh_interval())
            except ModuleNotFoundError:
                continue
        return min(intervals) if intervals else 1.0

    @classmethod
    def cleanup_all(cls) -> None:
        """清理所有模块资源。"""
        for instance in cls._instances.values():
            instance.cleanup()
        cls._instances.clear()


# 全局注册表实例
registry = ModuleRegistry()
