"""终端渲染器。

使用 prompt_toolkit 在终端内显示状态栏。
"""

import sys
import threading
from typing import Callable, Optional

from prompt_toolkit import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style

from cc_statusline.engine.statusline_engine import EngineConfig, StatuslineEngine
from cc_statusline.modules.base import ModuleOutput
from cc_statusline.theme.loader import ThemeLoader


def _is_tty() -> bool:
    """检查是否在 TTY 环境中运行。"""
    return sys.stdout.isatty()


class TerminalRenderer:
    """终端渲染器。

    使用 prompt_toolkit 在终端底部显示状态栏。
    """

    def __init__(
        self,
        engine: StatuslineEngine,
        theme_loader: Optional[ThemeLoader] = None,
    ) -> None:
        """初始化渲染器。

        Args:
            engine: 状态栏引擎
            theme_loader: 主题加载器
        """
        self._engine = engine
        self._theme_loader = theme_loader or ThemeLoader()
        self._app: Optional[Application] = None
        self._running = False
        self._lock = threading.Lock()
        self._output_text: str = ""
        self._update_callbacks: list[Callable[[str], None]] = []

    def _get_theme_style(self) -> Style:
        """获取主题样式。

        Returns:
            prompt_toolkit 样式
        """
        theme = self._engine.get_theme()
        if theme is None:
            theme = self._theme_loader.load("modern")

        colors = theme.get("colors", {})
        style_dict: dict[str, str] = {}

        # 状态栏默认样式 (fg:bg: 格式)
        bg = colors.get("background", "#1e1e2e")
        fg = colors.get("text", "#ffffff")
        style_dict["statusline.default"] = f"fg:{fg} bg:{bg}"

        # 颜色样式映射
        color_map = {
            "primary": colors.get("primary", "#00d4aa"),
            "success": colors.get("success", "#4ade80"),
            "warning": colors.get("warning", "#fbbf24"),
            "error": colors.get("error", "#ef4444"),
            "info": colors.get("info", "#3b82f6"),
            "dim": colors.get("dim", "#a0a0a0"),
        }

        for name, color in color_map.items():
            style_dict[f"statusline.{name}"] = f"fg:{color}"

        # 图标样式
        icon_styles = {
            "mcp": colors.get("primary", "#00d4aa"),
            "time": colors.get("accent", "#22d3ee"),
            "git": colors.get("warning", "#fbbf24"),
        }
        for name, color in icon_styles.items():
            style_dict[f"statusline.icon.{name}"] = f"fg:{color}"

        return Style.from_dict(style_dict)

    def _create_toolbar_content(self) -> FormattedText:  # noqa: C901
        """创建底部工具栏内容。

        Returns:
            格式化文本
        """
        theme = self._engine.get_theme()
        if theme is None:
            theme = self._theme_loader.load("modern")

        colors = theme.get("colors", {})
        icons = theme.get("icons", {})

        separator = icons.get("separator", " │ ")
        bg = colors.get("background", "#1e1e2e")
        fg = colors.get("text", "#ffffff")
        dim = colors.get("dim", "#a0a0a0")

        # 获取模块输出
        outputs = self._engine.get_outputs()
        parts: list[tuple[str, str]] = []

        for _name, output in outputs.items():
            if isinstance(output, ModuleOutput):
                # 确定颜色类
                color_class = "success"
                if output.status.value == "error":
                    color_class = "error"
                elif output.status.value == "warning":
                    color_class = "warning"
                elif output.status.value == "disabled":
                    color_class = "dim"

                # 构建文本
                text_parts = []
                if output.icon:
                    text_parts.append(f"[::statusline.icon.{_name}]{output.icon}[/]")
                if output.text:
                    text_parts.append(f"[::statusline.{color_class}]{output.text}[/]")

                if text_parts:
                    text = " ".join(text_parts)
                    parts.append((text, f"{fg} on {bg}"))
                    parts.append((separator, f"{dim} on {bg}"))

        # 移除最后的分隔符
        if parts and separator in [p[0] for p in parts]:
            # 找到并移除最后一个分隔符
            for i in range(len(parts) - 1, -1, -1):
                if parts[i][0] == separator:
                    parts.pop(i)
                    break

        if not parts:
            parts.append(("[::statusline.dim]无模块输出[/]", f"{dim} on {bg}"))

        return FormattedText(parts)

    def _create_bottom_toolbar(self) -> Window:
        """创建底部工具栏窗口。

        Returns:
            底部窗口
        """
        control = FormattedTextControl(
            self._create_toolbar_content,
            focusable=False,
        )
        return Window(
            control,
            height=1,
            style="class:statusline.default",
            char=" ",
        )

    def _create_key_bindings(self) -> KeyBindings:  # noqa: C901
        """创建按键绑定。

        Returns:
            按键绑定
        """
        from prompt_toolkit.key_binding import KeyPressEvent

        kb = KeyBindings()

        @kb.add("c-c", eager=True)
        def exit_app(event: KeyPressEvent) -> None:
            """Ctrl+C 退出。"""
            self._engine.stop()
            self._running = False
            if self._app:
                self._app.exit()

        @kb.add("q", eager=True)
        def quit_app(event: KeyPressEvent) -> None:
            """Q 键退出。"""
            self._engine.stop()
            self._running = False
            if self._app:
                self._app.exit()

        @kb.add("r", eager=True)
        def refresh(event: KeyPressEvent) -> None:
            """R 键刷新。"""
            self._engine.stop()
            self._engine.initialize()
            self._engine.start()

        @kb.add("t", eager=True)
        def toggle_theme(event: KeyPressEvent) -> None:
            """T 键切换主题。"""
            themes = self._theme_loader.list_available()
            current = self._engine.config.theme
            if current in themes:
                idx = themes.index(current)
                next_idx = (idx + 1) % len(themes)
                next_theme = themes[next_idx]
            else:
                next_theme = themes[0] if themes else "modern"

            self._engine.configure(theme=next_theme)
            self._engine.load_theme(next_theme)

        @kb.add("p", eager=True)
        def pause_resume(event: KeyPressEvent) -> None:
            """P 键暂停/恢复。"""
            if self._engine.state == "running":
                self._engine.pause()
            elif self._engine.state == "paused":
                self._engine.resume()

        return kb

    def run(self, full_screen: bool = False) -> None:
        """运行渲染器。

        Args:
            full_screen: 是否全屏模式
        """
        if not _is_tty():
            # 非 TTY 环境，输出到 stdout
            self._run_simple()
            return

        # 初始化引擎
        if self._engine.state == "stopped":
            self._engine.initialize()
            self._engine.start()

        self._running = True

        # 注册输出更新回调
        self._engine.on_output_update(self._on_output_update)

        # 创建布局
        layout = Layout(HSplit([self._create_bottom_toolbar()]))

        # 创建应用
        self._app = Application(
            layout=layout,
            key_bindings=self._create_key_bindings(),
            style=self._get_theme_style(),
            full_screen=full_screen,
            mouse_support=False,
        )

        # 运行应用
        try:
            self._app.run()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _run_simple(self) -> None:
        """简单模式运行（非 TTY）。"""
        if self._engine.state == "stopped":
            self._engine.initialize()
            self._engine.start()

        self._running = True

        try:
            while self._running:
                output = self._engine.get_combined_output()
                if output:
                    print(f"\r{output}", end="", flush=True)
                threading.Event().wait(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _on_output_update(self) -> None:
        """输出更新回调。"""
        output = self._engine.get_combined_output()
        with self._lock:
            self._output_text = output

        for callback in self._update_callbacks:
            try:
                callback(output)
            except Exception:
                pass

    def on_update(self, callback: Callable[[str], None]) -> None:
        """注册更新回调。

        Args:
            callback: 回调函数
        """
        self._update_callbacks.append(callback)

    def register_update_callback(self, callback: Callable[[str], None]) -> None:
        """注册更新回调（别名）。

        Args:
            callback: 回调函数
        """
        self.on_update(callback)

    def unregister_update_callback(self, callback: Callable[[str], None]) -> None:
        """注销更新回调。

        Args:
            callback: 回调函数
        """
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)

    def _update_output_text(self, text: str) -> None:
        """更新输出文本。

        Args:
            text: 新的输出文本
        """
        with self._lock:
            self._output_text = text

    def get_output_text(self) -> str:
        """获取当前输出文本。

        Returns:
            输出文本
        """
        with self._lock:
            return self._output_text

    def is_running(self) -> bool:
        """检查渲染器是否正在运行。

        Returns:
            是否正在运行
        """
        return self._running

    def _notify_callbacks(self, text: str) -> None:
        """通知所有回调。

        Args:
            text: 要通知的文本
        """
        for callback in self._update_callbacks:
            try:
                callback(text)
            except Exception:
                pass

    def _format_output(self, outputs: list) -> str:
        """格式化输出。

        Args:
            outputs: 输出列表

        Returns:
            格式化后的字符串
        """
        if not outputs:
            return ""

        parts = []
        for output in outputs:
            if isinstance(output, ModuleOutput):
                text = str(output)
                if text:
                    parts.append(text)

        separator = " │ "
        return separator.join(parts)

    def _create_statusline_control(self):
        """创建状态栏控件。

        Returns:
            状态栏控件
        """
        from prompt_toolkit.layout.controls import FormattedTextControl

        return FormattedTextControl(
            self._create_toolbar_content,
            focusable=False,
        )

    def _create_layout(self):
        """创建布局。

        Returns:
            布局对象
        """
        from prompt_toolkit.layout.containers import HSplit, Window
        from prompt_toolkit.layout.layout import Layout

        control = self._create_statusline_control()
        window = Window(
            control,
            height=1,
            style="class:statusline.default",
            char=" ",
        )
        return Layout(HSplit([window]))

    def refresh_output(self) -> None:
        """刷新输出。"""
        self._on_output_update()

    def get_output(self) -> str:
        """获取当前输出。

        Returns:
            输出文本
        """
        with self._lock:
            return self._output_text

    def stop(self) -> None:
        """停止渲染器。"""
        self._running = False
        self._engine.stop()

    def render_once(self) -> str:
        """单次渲染。

        Returns:
            渲染输出
        """
        return self._engine.get_combined_output()


def create_statusline(
    theme: str = "modern",
    modules: Optional[list[str]] = None,
    display_mode: str = "terminal",
) -> TerminalRenderer:
    """创建状态栏渲染器。

    Args:
        theme: 主题名称
        modules: 模块列表
        display_mode: 显示模式

    Returns:
        终端渲染器实例
    """
    from cc_statusline.engine.statusline_engine import DisplayMode

    config = EngineConfig(
        theme=theme,
        modules=modules or ["mcp_status", "session_time"],
        display_mode=DisplayMode(display_mode),
    )

    engine = StatuslineEngine(config)
    renderer = TerminalRenderer(engine)

    return renderer
