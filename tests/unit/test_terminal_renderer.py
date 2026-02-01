"""终端渲染器单元测试"""

from unittest.mock import MagicMock, patch

from cc_status.engine import EngineConfig, StatuslineEngine
from cc_status.modules.base import ModuleOutput, ModuleStatus
from cc_status.render.terminal_renderer import TerminalRenderer, _is_tty


class TestIsTTY:
    """TTY 检查测试类"""

    def test_is_tty_true(self) -> None:
        """测试 TTY 环境（返回 True）"""
        with patch("sys.stdout.isatty", return_value=True):
            assert _is_tty() is True

    def test_is_tty_false(self) -> None:
        """测试非 TTY 环境（返回 False）"""
        with patch("sys.stdout.isatty", return_value=False):
            assert _is_tty() is False


class TestTerminalRenderer:
    """终端渲染器测试类"""

    def test_init(self) -> None:
        """测试初始化"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        assert renderer._engine is engine
        assert renderer._app is None
        assert renderer._running is False
        assert renderer._output_text == ""
        assert renderer._update_callbacks == []

    def test_init_with_theme_loader(self) -> None:
        """测试初始化（带主题加载器）"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        mock_loader = MagicMock()

        renderer = TerminalRenderer(engine, mock_loader)

        assert renderer._theme_loader is mock_loader

    def test_get_theme_style_default_theme(self) -> None:
        """测试获取主题样式（默认主题）"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        style = renderer._get_theme_style()

        # 验证样式对象
        assert style is not None

    def test_get_theme_style_engine_theme(self) -> None:
        """测试获取主题样式（引擎主题）"""
        config = EngineConfig(theme="cyberpunk")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        style = renderer._get_theme_style()

        # 验证样式对象
        assert style is not None

    def test_format_output_basic(self) -> None:
        """测试格式化基本输出"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        output = ModuleOutput(
            text="测试文本",
            icon="🔌",
            color="green",
            status=ModuleStatus.SUCCESS,
        )

        formatted = renderer._format_output([output])

        assert "测试文本" in formatted
        assert "🔌" in formatted

    def test_format_output_multiple(self) -> None:
        """测试格式化多个输出"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        outputs = [
            ModuleOutput(
                text="MCP 服务器",
                icon="🔌",
                color="green",
                status=ModuleStatus.SUCCESS,
            ),
            ModuleOutput(
                text="2h 30m",
                icon="⏱️",
                color="blue",
                status=ModuleStatus.SUCCESS,
            ),
        ]

        formatted = renderer._format_output(outputs)

        assert "MCP 服务器" in formatted
        assert "🔌" in formatted
        assert "2h 30m" in formatted
        assert "⏱️" in formatted

    def test_format_output_empty(self) -> None:
        """测试格式化空输出"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        formatted = renderer._format_output([])

        assert formatted == ""

    def test_register_update_callback(self) -> None:
        """测试注册更新回调"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        callback = MagicMock()
        renderer.register_update_callback(callback)

        assert callback in renderer._update_callbacks

    def test_unregister_update_callback(self) -> None:
        """测试注销更新回调"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        callback = MagicMock()
        renderer.register_update_callback(callback)
        renderer.unregister_update_callback(callback)

        assert callback not in renderer._update_callbacks

    def test_update_output_text(self) -> None:
        """测试更新输出文本"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        renderer._update_output_text("新的状态栏文本")

        assert renderer._output_text == "新的状态栏文本"

    def test_get_output_text(self) -> None:
        """测试获取输出文本"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        renderer._output_text = "测试文本"
        assert renderer.get_output_text() == "测试文本"

    def test_is_running(self) -> None:
        """测试运行状态"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        assert renderer.is_running() is False

        renderer._running = True
        assert renderer.is_running() is True

    def test_stop(self) -> None:
        """测试停止渲染"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        renderer._running = True
        renderer._app = MagicMock()

        renderer.stop()

        assert renderer._running is False

    def test_notify_callbacks(self) -> None:
        """测试通知回调"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        callback1 = MagicMock()
        callback2 = MagicMock()

        renderer.register_update_callback(callback1)
        renderer.register_update_callback(callback2)

        renderer._notify_callbacks("测试通知")

        callback1.assert_called_once_with("测试通知")
        callback2.assert_called_once_with("测试通知")

    def test_create_statusline_control(self) -> None:
        """测试创建状态栏控件"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        control = renderer._create_statusline_control()

        assert control is not None

    def test_create_layout(self) -> None:
        """测试创建布局"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        layout = renderer._create_layout()

        assert layout is not None

    def test_create_key_bindings(self) -> None:
        """测试创建键绑定"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        bindings = renderer._create_key_bindings()

        assert bindings is not None

    def test_render_once(self) -> None:
        """测试单次渲染"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        # 不应该抛出异常
        renderer.render_once()

    def test_refresh_output(self) -> None:
        """测试刷新输出"""
        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)
        renderer = TerminalRenderer(engine)

        # 不应该抛出异常
        renderer.refresh_output()


class TestCreateStatusline:
    """创建状态栏函数测试类"""

    @patch("cc_status.render.terminal_renderer.TerminalRenderer")
    def test_create_statusline(self, mock_renderer_class: MagicMock) -> None:
        """测试创建状态栏"""
        from cc_status.render.terminal_renderer import create_statusline

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        config = EngineConfig(theme="modern")
        engine = StatuslineEngine(config)

        renderer = create_statusline(engine)

        assert renderer is not None
        mock_renderer_class.assert_called_once()
