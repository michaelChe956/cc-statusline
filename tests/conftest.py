"""pytest 配置和共享 fixtures"""

from typing import Any

import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch


# ============ 原有 fixtures ============
@pytest.fixture
def sample_config() -> dict[str, Any]:
    """提供测试用的示例配置"""
    return {"name": "test", "value": 42}


# ============ 单例重置 fixtures ============
@pytest.fixture(autouse=True)
def reset_singletons():
    """自动重置所有单例（每个测试前）"""
    from cc_statusline.modules.registry import ModuleRegistry
    from cc_statusline.engine.statusline_engine import reset_engine

    ModuleRegistry.reset()
    reset_engine()
    yield
    ModuleRegistry.reset()
    reset_engine()


# ============ Mock fixtures ============
@pytest.fixture
def mock_time_sleep():
    """模拟 time.sleep，避免测试中的真实延迟"""
    with patch("time.sleep") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_threading_thread():
    """模拟 threading.Thread，控制线程行为"""
    with patch("threading.Thread") as mock_thread:
        mock_instance = MagicMock()
        mock_instance.start = MagicMock()
        mock_instance.join = MagicMock()
        mock_instance.is_alive = MagicMock(return_value=False)
        mock_thread.return_value = mock_instance
        yield mock_thread


# ============ 文件 fixtures ============
@pytest.fixture
def temp_theme_file(tmp_path: Path) -> Path:
    """创建临时主题文件"""
    theme_data = {
        "name": "TestTheme",
        "description": "测试主题",
        "colors": {
            "primary": "#00ff00",
            "success": "#4ade80",
            "warning": "#fbbf24",
            "error": "#ef4444",
            "info": "#3b82f6",
            "text": "#ffffff",
        },
        "icons": {
            "mcp": "M",
            "time": "T",
            "separator": " │ ",
        },
        "styles": {
            "module": {
                "separator": " │ ",
                "prefix": "",
                "suffix": "",
            }
        },
    }
    theme_file = tmp_path / "test_theme.yaml"
    theme_file.write_text(yaml.dump(theme_data))
    return theme_file


@pytest.fixture
def invalid_yaml_file(tmp_path: Path) -> Path:
    """创建无效的 YAML 文件"""
    invalid_file = tmp_path / "invalid.yaml"
    invalid_file.write_text("{ invalid yaml content: ")
    return invalid_file


# ============ 模块相关 fixtures ============
@pytest.fixture
def valid_module_output():
    """创建有效的 ModuleOutput"""
    from cc_statusline.modules.base import ModuleOutput, ModuleStatus

    return ModuleOutput(
        text="Test Output", icon="T", color="green", status=ModuleStatus.SUCCESS
    )


@pytest.fixture
def mock_base_module():
    """创建通用的模拟模块"""
    from cc_statusline.modules.base import (
        ModuleMetadata,
        ModuleOutput,
        ModuleStatus,
    )

    module = MagicMock()
    module.metadata = ModuleMetadata(name="test_module", description="测试模块")
    module.is_available.return_value = True
    module.get_refresh_interval.return_value = 1000
    module.initialize.return_value = None
    module.refresh.return_value = None
    module.get_output.return_value = ModuleOutput(
        text="Test", icon="T", color="green", status=ModuleStatus.SUCCESS
    )
    module.cleanup.return_value = None
    return module


@pytest.fixture
def sample_module_class():
    """创建示例模块类用于注册表测试"""
    from cc_statusline.modules.base import (
        BaseModule,
        ModuleMetadata,
        ModuleOutput,
        ModuleStatus,
    )

    class SampleModule:
        metadata = ModuleMetadata(name="sample", description="示例模块")

        def initialize(self) -> None:
            pass

        def refresh(self) -> None:
            pass

        def get_output(self) -> ModuleOutput:
            return ModuleOutput(text="Sample", icon="S")

        def cleanup(self) -> None:
            pass

        def is_available(self) -> bool:
            return True

        def get_refresh_interval(self) -> float:
            return 1.0

    return SampleModule


# ============ 引擎相关 fixtures ============
@pytest.fixture
def engine_config():
    """创建引擎配置"""
    from cc_statusline.engine.statusline_engine import EngineConfig

    return EngineConfig(theme="modern", refresh_interval=1.0)


@pytest.fixture
def engine(engine_config):
    """创建引擎实例"""
    from cc_statusline.engine.statusline_engine import StatuslineEngine

    eng = StatuslineEngine(engine_config)
    yield eng
    if eng.state != "stopped":
        eng.stop()


@pytest.fixture
def theme_loader():
    """创建主题加载器实例"""
    from cc_statusline.theme.loader import ThemeLoader

    return ThemeLoader()


@pytest.fixture
def scheduler():
    """创建调度器实例"""
    from cc_statusline.engine.scheduler import Scheduler

    sch = Scheduler()
    yield sch
    if sch.get_state().value != "stopped":
        sch.stop()
