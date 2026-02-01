"""会话时间模块单元测试"""

from datetime import timedelta

from cc_status.modules.base import ModuleStatus


class TestSessionTimeModuleLogic:
    """会话时间模块逻辑测试（不依赖导入）"""

    def test_metadata_values(self) -> None:
        """测试模块元数据值"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()
        metadata = module.metadata

        assert metadata.name == "session_time"
        assert metadata.description == "显示当前会话使用时间"
        assert metadata.version == "1.2.0"
        assert metadata.author == "Claude Code"
        assert metadata.enabled is True

    def test_calculate_elapsed_with_context(self) -> None:
        """测试从上下文计算经过时间"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        # 设置上下文（12.5 小时 = 45000000 毫秒）
        context = {"cost": {"total_duration_ms": 45000000}}
        module.set_context(context)

        elapsed = module._calculate_elapsed()

        assert elapsed is not None
        assert elapsed.total_seconds() == 45000
        assert elapsed == timedelta(hours=12, minutes=30)

    def test_calculate_elapsed_no_context(self) -> None:
        """测试无上下文时返回 None"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        elapsed = module._calculate_elapsed()

        assert elapsed is None

    def test_format_elapsed_hours(self) -> None:
        """测试短格式时间（小时）"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()
        elapsed = timedelta(hours=2, minutes=30)

        assert module._format_elapsed(elapsed) == "2h 30m"

    def test_format_elapsed_minutes(self) -> None:
        """测试短格式时间（分钟）"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()
        elapsed = timedelta(minutes=15, seconds=30)

        assert module._format_elapsed(elapsed) == "15m 30s"

    def test_format_elapsed_seconds(self) -> None:
        """测试短格式时间（秒）"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()
        elapsed = timedelta(seconds=45)

        assert module._format_elapsed(elapsed) == "45s"

    def test_reset(self) -> None:
        """测试重置计时"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        module._last_elapsed = timedelta(hours=5)
        module._total_duration_ms = 18000000

        module.reset()

        assert module._last_elapsed is None
        assert module._total_duration_ms is None

    def test_get_output_no_elapsed(self) -> None:
        """测试获取输出（无时间数据）"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        output = module.get_output()

        assert output.text == "--:--"
        assert output.icon == "⏱️"
        assert output.color == "gray"
        assert output.status == ModuleStatus.SUCCESS

    def test_get_output_short_session(self) -> None:
        """测试获取输出（短会话 < 1h）"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        context = {"cost": {"total_duration_ms": 1800000}}
        module.set_context(context)

        output = module.get_output()

        assert "30m" in output.text
        assert output.color == "blue"

    def test_get_output_medium_session(self) -> None:
        """测试获取输出（中等会话 1-2h）"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        context = {"cost": {"total_duration_ms": 5400000}}
        module.set_context(context)

        output = module.get_output()

        assert "1h" in output.text
        assert output.color == "yellow"

    def test_get_output_long_session(self) -> None:
        """测试获取输出（长会话 >= 2h）"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        context = {"cost": {"total_duration_ms": 10800000}}
        module.set_context(context)

        output = module.get_output()

        assert "3h" in output.text
        assert output.color == "green"

    def test_is_available(self) -> None:
        """测试模块可用性检查"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()
        assert module.is_available() is True

    def test_get_refresh_interval(self) -> None:
        """测试获取刷新间隔"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()
        assert module.get_refresh_interval() == 1.0

    def test_refresh(self) -> None:
        """测试刷新功能"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()
        module.set_context({"cost": {"total_duration_ms": 3600000}})
        module.refresh()

        assert module._last_elapsed is not None
        assert module._last_elapsed.total_seconds() == 3600

    def test_set_context(self) -> None:
        """测试设置上下文数据"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        context = {
            "hook_event_name": "Status",
            "session_id": "abc123",
            "cost": {
                "total_cost_usd": 0.01234,
                "total_duration_ms": 45000000,
            },
        }

        module.set_context(context)

        assert module._context == context
        assert module._total_duration_ms == 45000000

    def test_set_context_empty(self) -> None:
        """测试设置空上下文"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        module.set_context({})

        assert module._context == {}
        assert module._total_duration_ms is None

    def test_get_output_tooltip(self) -> None:
        """测试 tooltip 显示"""
        from cc_status.modules.session_time import SessionTimeModule

        module = SessionTimeModule()

        context = {"cost": {"total_duration_ms": 7200000}}
        module.set_context(context)

        output = module.get_output()

        assert output.tooltip == "会话时长: 2h 0m"
