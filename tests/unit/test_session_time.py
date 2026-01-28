"""会话时间模块单元测试"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cc_statusline.modules.session_time import SessionTimeModule
from cc_statusline.modules.base import ModuleStatus


class TestSessionTimeModule:
    """会话时间模块测试类"""

    def test_metadata(self) -> None:
        """测试模块元数据"""
        module = SessionTimeModule()
        metadata = module.metadata

        assert metadata.name == "session_time"
        assert metadata.description == "显示当前会话使用时间"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Claude Code"
        assert metadata.enabled is True

    def test_initialization(self) -> None:
        """测试模块初始化"""
        module = SessionTimeModule()
        module.initialize()

        assert module._start_time is not None
        assert isinstance(module._start_time, datetime)
        assert module._paused is False
        assert module._format == "short"

    @patch("cc_statusline.modules.session_time.os.path.exists")
    @patch("builtins.open")
    def test_load_state(self, mock_open: MagicMock, mock_exists: MagicMock) -> None:
        """测试加载状态"""
        mock_exists.return_value = True
        test_state = {
            "start_time": "2024-01-15T10:30:00",
            "format": "long",
        }
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(test_state)

        module = SessionTimeModule()
        module._load_state()

        assert module._start_time is not None
        assert module._format == "long"

    @patch("cc_statusline.modules.session_time.os.path.exists")
    def test_load_state_no_file(self, mock_exists: MagicMock) -> None:
        """测试加载状态（文件不存在）"""
        mock_exists.return_value = False

        module = SessionTimeModule()
        module._load_state()

        assert module._start_time is None
        assert module._format == "short"

    @patch("builtins.open")
    def test_save_state(self, mock_open: MagicMock) -> None:
        """测试保存状态"""
        module = SessionTimeModule()
        module._start_time = datetime(2024, 1, 15, 10, 30, 0)
        module._format = "long"

        module._save_state()

        # 验证文件被写入
        mock_open.assert_called_once()
        mock_open.return_value.__enter__.return_value.write.assert_called()

    def test_calculate_elapsed(self) -> None:
        """测试计算经过时间"""
        module = SessionTimeModule()
        module._start_time = datetime.now() - timedelta(hours=2, minutes=30)

        elapsed = module._calculate_elapsed()

        assert elapsed is not None
        assert elapsed.total_seconds() >= 9000  # 至少 2.5 小时

    def test_calculate_elapsed_no_start_time(self) -> None:
        """测试计算经过时间（无开始时间）"""
        module = SessionTimeModule()
        module._start_time = None

        elapsed = module._calculate_elapsed()
        assert elapsed is None

    def test_format_elapsed_short_format_hours(self) -> None:
        """测试短格式时间（小时）"""
        module = SessionTimeModule()
        elapsed = timedelta(hours=2, minutes=30)

        formatted = module._format_elapsed(elapsed)
        assert formatted == "2h 30m"

    def test_format_elapsed_short_format_minutes(self) -> None:
        """测试短格式时间（分钟）"""
        module = SessionTimeModule()
        elapsed = timedelta(minutes=15, seconds=30)

        formatted = module._format_elapsed(elapsed)
        assert formatted == "15m 30s"

    def test_format_elapsed_short_format_seconds(self) -> None:
        """测试短格式时间（秒）"""
        module = SessionTimeModule()
        elapsed = timedelta(seconds=45)

        formatted = module._format_elapsed(elapsed)
        assert formatted == "45s"

    def test_format_elapsed_long_format(self) -> None:
        """测试长格式时间"""
        module = SessionTimeModule()
        module._format = "long"
        elapsed = timedelta(hours=2, minutes=30, seconds=45)

        formatted = module._format_elapsed(elapsed)
        assert formatted == "02:30:45"

    def test_set_format_short(self) -> None:
        """测试设置短格式"""
        module = SessionTimeModule()
        module.set_format("short")
        assert module._format == "short"

    def test_set_format_long(self) -> None:
        """测试设置长格式"""
        module = SessionTimeModule()
        module.set_format("long")
        assert module._format == "long"

    def test_set_format_invalid(self) -> None:
        """测试设置无效格式"""
        module = SessionTimeModule()
        original_format = module._format
        module.set_format("invalid")
        assert module._format == original_format

    def test_get_elapsed(self) -> None:
        """测试获取经过时间"""
        module = SessionTimeModule()
        module._start_time = datetime.now() - timedelta(minutes=30)
        module.refresh()  # 需要刷新才能计算时间

        elapsed = module.get_elapsed()
        assert elapsed is not None
        assert elapsed.total_seconds() >= 1800  # 至少 30 分钟

    def test_reset(self) -> None:
        """测试重置计时"""
        module = SessionTimeModule()
        module._start_time = datetime(2024, 1, 1, 0, 0, 0)
        module._last_elapsed = timedelta(hours=5)

        module.reset()

        assert module._start_time is not None
        assert module._last_elapsed is None
        # 新的开始时间应该在重置时间附近
        time_diff = datetime.now() - module._start_time
        assert time_diff.total_seconds() < 5  # 5 秒内

    def test_get_output_no_elapsed(self) -> None:
        """测试获取输出（无时间数据）"""
        module = SessionTimeModule()
        module._start_time = None

        output = module.get_output()
        assert output.text == "--:--"
        assert output.icon == "⏱️"
        assert output.color == "gray"
        assert output.status == ModuleStatus.SUCCESS

    def test_get_output_short_session(self) -> None:
        """测试获取输出（短会话 < 1h）"""
        module = SessionTimeModule()
        module._start_time = datetime.now() - timedelta(minutes=30)

        output = module.get_output()
        assert "30m" in output.text
        assert output.icon == "⏱️"
        assert output.color == "blue"
        assert output.status == ModuleStatus.SUCCESS

    def test_get_output_medium_session(self) -> None:
        """测试获取输出（中等会话 1-2h）"""
        module = SessionTimeModule()
        module._start_time = datetime.now() - timedelta(hours=1, minutes=30)

        output = module.get_output()
        assert "1h" in output.text
        assert output.icon == "⏱️"
        assert output.color == "yellow"
        assert output.status == ModuleStatus.SUCCESS

    def test_get_output_long_session(self) -> None:
        """测试获取输出（长会话 >= 2h）"""
        module = SessionTimeModule()
        module._start_time = datetime.now() - timedelta(hours=3)

        output = module.get_output()
        assert "3h" in output.text
        assert output.icon == "⏱️"
        assert output.color == "green"
        assert output.status == ModuleStatus.SUCCESS

    def test_get_start_time(self) -> None:
        """测试获取开始时间"""
        module = SessionTimeModule()
        start = datetime(2024, 1, 15, 10, 30, 0)
        module._start_time = start

        assert module.get_start_time() == start

    def test_get_formatted_start_time(self) -> None:
        """测试获取格式化的开始时间"""
        module = SessionTimeModule()
        module._start_time = datetime(2024, 1, 15, 10, 30, 45)

        formatted = module.get_formatted_start_time()
        assert formatted == "10:30:45"

    def test_get_formatted_start_time_no_start(self) -> None:
        """测试获取格式化的开始时间（无开始时间）"""
        module = SessionTimeModule()
        module._start_time = None

        formatted = module.get_formatted_start_time()
        assert formatted == "未知"

    def test_is_available(self) -> None:
        """测试模块可用性检查"""
        module = SessionTimeModule()
        assert module.is_available() is True

    def test_get_refresh_interval(self) -> None:
        """测试获取刷新间隔"""
        module = SessionTimeModule()
        assert module.get_refresh_interval() == 1.0

    @patch("builtins.open")
    def test_cleanup(self, mock_open: MagicMock) -> None:
        """测试清理资源"""
        module = SessionTimeModule()
        module._start_time = datetime.now()
        module._format = "long"

        module.cleanup()

        # 验证状态被保存
        mock_open.assert_called_once()

    def test_refresh(self) -> None:
        """测试刷新功能"""
        module = SessionTimeModule()
        module.initialize()
        module.refresh()
        assert module._last_elapsed is not None
