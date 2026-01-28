"""模块基类单元测试"""

import pytest

from cc_statusline.modules.base import (
    ModuleError,
    ModuleLoadError,
    ModuleMetadata,
    ModuleNotFoundError,
    ModuleOutput,
    ModuleStatus,
)


class TestModuleStatus:
    """ModuleStatus 枚举测试"""

    def test_status_values(self) -> None:
        """测试状态枚举值"""
        assert ModuleStatus.SUCCESS.value == "success"
        assert ModuleStatus.WARNING.value == "warning"
        assert ModuleStatus.ERROR.value == "error"
        assert ModuleStatus.DISABLED.value == "disabled"

    def test_status_comparison(self) -> None:
        """测试状态比较"""
        assert ModuleStatus.SUCCESS == ModuleStatus.SUCCESS
        assert ModuleStatus.SUCCESS != ModuleStatus.ERROR


class TestModuleOutput:
    """ModuleOutput 数据类测试"""

    def test_init_default_values(self) -> None:
        """测试默认值初始化"""
        output = ModuleOutput(text="Test")
        assert output.text == "Test"
        assert output.icon == ""
        assert output.color == ""
        assert output.status == ModuleStatus.SUCCESS
        assert output.tooltip == ""
        assert output.style == ""

    def test_init_with_all_params(self) -> None:
        """测试完整参数初始化"""
        output = ModuleOutput(
            text="Test",
            icon="T",
            color="green",
            status=ModuleStatus.WARNING,
            tooltip="Hint",
            style="bold",
        )
        assert output.text == "Test"
        assert output.icon == "T"
        assert output.color == "green"
        assert output.status == ModuleStatus.WARNING
        assert output.tooltip == "Hint"
        assert output.style == "bold"

    def test_to_dict_conversion(self) -> None:
        """测试转换为字典"""
        output = ModuleOutput(text="Test", icon="T", color="red")
        result = output.to_dict()
        assert result["text"] == "Test"
        assert result["icon"] == "T"
        assert result["color"] == "red"
        assert result["status"] == "success"

    def test_str_representation(self) -> None:
        """测试字符串表示"""
        output = ModuleOutput(text="Test", icon="T")
        assert str(output) == "T Test"

        output_no_icon = ModuleOutput(text="Test")
        assert str(output_no_icon) == "Test"

    def test_equality(self) -> None:
        """测试相等性"""
        output1 = ModuleOutput(text="Test")
        output2 = ModuleOutput(text="Test")
        assert output1.text == output2.text


class TestModuleMetadata:
    """ModuleMetadata 数据类测试"""

    def test_init_minimal(self) -> None:
        """测试最小参数初始化"""
        metadata = ModuleMetadata(name="test", description="测试")
        assert metadata.name == "test"
        assert metadata.description == "测试"
        assert metadata.version == "1.0.0"
        assert metadata.author == ""
        assert metadata.enabled is True
        assert metadata.dependencies == []

    def test_init_full(self) -> None:
        """测试完整参数初始化"""
        metadata = ModuleMetadata(
            name="test",
            description="测试",
            version="2.0.0",
            author="Author",
            enabled=False,
            dependencies=["dep1", "dep2"],
        )
        assert metadata.name == "test"
        assert metadata.description == "测试"
        assert metadata.version == "2.0.0"
        assert metadata.author == "Author"
        assert metadata.enabled is False
        assert len(metadata.dependencies) == 2

    def test_property_access(self) -> None:
        """测试属性访问"""
        metadata = ModuleMetadata(name="test", description="测试")
        assert metadata.name == "test"
        assert metadata.description == "测试"


class TestModuleErrors:
    """模块异常测试"""

    def test_module_error_creation(self) -> None:
        """测试模块错误创建"""
        error = ModuleError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_module_not_found_error(self) -> None:
        """测试模块未找到错误"""
        error = ModuleNotFoundError("Module 'test' not found")
        assert str(error) == "Module 'test' not found"
        assert isinstance(error, ModuleError)

    def test_module_load_error(self) -> None:
        """测试模块加载错误"""
        error = ModuleLoadError("Failed to load module")
        assert str(error) == "Failed to load module"
        assert isinstance(error, ModuleError)
