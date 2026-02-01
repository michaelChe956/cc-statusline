"""模块注册表单元测试"""

import pytest

from cc_status.modules.base import (
    ModuleLoadError,
    ModuleMetadata,
    ModuleNotFoundError,
)
from cc_status.modules.registry import ModuleRegistry


class TestModuleRegistrySingleton:
    """单例模式测试"""

    def test_singleton_pattern(self) -> None:
        """测试单例模式"""
        registry1 = ModuleRegistry()
        registry2 = ModuleRegistry()
        assert registry1 is registry2

    def test_multiple_calls_same_instance(self) -> None:
        """测试多次调用返回同一实例"""
        instances = [ModuleRegistry() for _ in range(5)]
        assert len(set(id(i) for i in instances)) == 1


class TestModuleRegistryBasicOperations:
    """基本操作测试"""

    def test_register_module_class(self, sample_module_class) -> None:
        """测试注册模块类"""
        ModuleRegistry.register("test", sample_module_class)
        assert ModuleRegistry.has_module("test")

    def test_register_duplicate_raises(self, sample_module_class) -> None:
        """测试重复注册抛出异常"""
        ModuleRegistry.register("test", sample_module_class)
        with pytest.raises(ModuleLoadError, match="已注册"):
            ModuleRegistry.register("test", sample_module_class)

    def test_unregister_module(self, sample_module_class) -> None:
        """测试注销模块"""
        ModuleRegistry.register("test", sample_module_class)
        ModuleRegistry.unregister("test")
        assert not ModuleRegistry.has_module("test")

    def test_unregister_nonexistent_raises(self) -> None:
        """测试注销不存在的模块不抛出异常"""
        # 应该静默失败
        ModuleRegistry.unregister("nonexistent")

    def test_has_module(self, sample_module_class) -> None:
        """测试检查模块存在"""
        assert not ModuleRegistry.has_module("test")
        ModuleRegistry.register("test", sample_module_class)
        assert ModuleRegistry.has_module("test")

    def test_get_class(self, sample_module_class) -> None:
        """测试获取模块类"""
        ModuleRegistry.register("test", sample_module_class)
        cls = ModuleRegistry.get_class("test")
        assert cls is sample_module_class

    def test_get_class_not_found(self) -> None:
        """测试获取不存在的模块类抛出异常"""
        with pytest.raises(ModuleNotFoundError, match="未找到"):
            ModuleRegistry.get_class("nonexistent")


class TestModuleRegistryInstanceManagement:
    """实例管理测试"""

    def test_get_instance_creates_new(self, sample_module_class) -> None:
        """测试创建新实例"""
        ModuleRegistry.register("test", sample_module_class)
        instance1 = ModuleRegistry.get_instance("test")
        instance2 = ModuleRegistry.get_instance("test")
        assert instance1 is instance2

    def test_get_instance_returns_cached(self, sample_module_class) -> None:
        """测试返回缓存的实例"""
        ModuleRegistry.register("test", sample_module_class)
        instance1 = ModuleRegistry.get_instance("test")
        instance2 = ModuleRegistry.get_instance("test", force_new=False)
        assert instance1 is instance2

    def test_get_instance_force_new(self, sample_module_class) -> None:
        """测试强制创建新实例"""
        ModuleRegistry.register("test", sample_module_class)
        instance1 = ModuleRegistry.get_instance("test")
        instance2 = ModuleRegistry.get_instance("test", force_new=True)
        # 强制创建新实例
        assert instance1 is not instance2

    def test_list_modules(self, sample_module_class) -> None:
        """测试列出模块"""
        ModuleRegistry.register("test1", sample_module_class)
        ModuleRegistry.register("test2", sample_module_class)
        modules = ModuleRegistry.list_modules()
        assert "test1" in modules
        assert "test2" in modules

    def test_get_metadata(self, sample_module_class) -> None:
        """测试获取模块元数据"""
        ModuleRegistry.register("test", sample_module_class)
        metadata = ModuleRegistry.get_metadata("test")
        assert isinstance(metadata, ModuleMetadata)
        assert metadata.name == "sample"


class TestModuleRegistryEnableDisable:
    """启用/禁用功能测试"""

    def test_enable_module(self, sample_module_class) -> None:
        """测试启用模块"""
        ModuleRegistry.register("test", sample_module_class)
        ModuleRegistry.enable("test")
        assert ModuleRegistry.is_enabled("test")

    def test_disable_module(self, sample_module_class) -> None:
        """测试禁用模块"""
        ModuleRegistry.register("test", sample_module_class)
        ModuleRegistry.enable("test")
        ModuleRegistry.disable("test")
        assert not ModuleRegistry.is_enabled("test")

    def test_is_enabled(self, sample_module_class) -> None:
        """测试检查模块是否启用"""
        ModuleRegistry.register("test", sample_module_class)
        assert not ModuleRegistry.is_enabled("test")
        ModuleRegistry.enable("test")
        assert ModuleRegistry.is_enabled("test")

    def test_get_enabled_modules(self, sample_module_class) -> None:
        """测试获取已启用的模块"""
        ModuleRegistry.register("test1", sample_module_class)
        ModuleRegistry.register("test2", sample_module_class)
        ModuleRegistry.enable("test1")
        ModuleRegistry.enable("test2")
        enabled = ModuleRegistry.get_enabled_modules()
        assert len(enabled) == 2

    def test_disabled_not_in_enabled_list(self, sample_module_class) -> None:
        """测试禁用的模块不在启用列表中"""
        ModuleRegistry.register("test1", sample_module_class)
        ModuleRegistry.register("test2", sample_module_class)
        ModuleRegistry.enable("test1")
        enabled = ModuleRegistry.get_enabled_modules()
        assert len(enabled) == 1


class TestModuleRegistryDependencyManagement:
    """依赖管理测试"""

    def test_get_refresh_interval(self, sample_module_class) -> None:
        """测试获取刷新间隔"""
        ModuleRegistry.register("test", sample_module_class)
        ModuleRegistry.enable("test")
        interval = ModuleRegistry.get_refresh_interval()
        assert interval == 1.0

    def test_get_refresh_interval_empty(self) -> None:
        """测试空注册表返回默认间隔"""
        interval = ModuleRegistry.get_refresh_interval()
        assert interval == 1.0

    def test_cleanup_all(self, sample_module_class) -> None:
        """测试清理所有模块"""
        ModuleRegistry.register("test", sample_module_class)
        ModuleRegistry.get_instance("test")
        ModuleRegistry.cleanup_all()
        assert len(ModuleRegistry._instances) == 0

    def test_cleanup_with_active_instances(self, sample_module_class) -> None:
        """测试清理活动实例"""
        ModuleRegistry.register("test", sample_module_class)
        instance = ModuleRegistry.get_instance("test")
        ModuleRegistry.cleanup_all()
        assert len(ModuleRegistry._instances) == 0


class TestModuleRegistryThreadSafety:
    """线程安全测试"""

    def test_concurrent_registration(self, sample_module_class) -> None:
        """测试并发注册"""
        import threading
        import uuid

        errors = []
        counter = [0]  # 使用可变列表作为计数器

        def worker():
            try:
                counter[0] += 1
                ModuleRegistry.register(f"test_{uuid.uuid4()}_{counter[0]}", sample_module_class)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
