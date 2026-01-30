"""Powerline 风格渲染器。

提供 Powerline 风格的状态栏渲染，支持箭头分隔符和多行布局。
"""

from dataclasses import dataclass
from typing import Any, Optional

from cc_statusline.modules.base import ModuleOutput, ModuleStatus
from cc_statusline.theme.loader import ThemeLoader


@dataclass
class PowerlineSegment:
    """Powerline 分段。"""

    text: str
    bg_color: str
    fg_color: str
    icon: str = ""


class PowerlineRenderer:
    """Powerline 风格渲染器。

    支持箭头分隔符、分段背景色和多行布局。
    """

    # Powerline 分隔符字符
    SEPARATORS = {
        "arrow": "\ue0b0",  # 
        "arrow_thin": "\ue0b1",  # 
        "round": "\ue0b4",  # 
        "round_thin": "\ue0b5",  # 
        "slant": "\ue0b8",  # 
        "slant_thin": "\ue0b9",  # 
        "curve": "\ue0aa",  # 
        "curve_thin": "\ue0ab",  # 
        "none": " ",
    }

    # ANSI 颜色映射
    COLOR_MAP = {
        "black": "0",
        "red": "1",
        "green": "2",
        "yellow": "3",
        "blue": "4",
        "purple": "5",  # magenta
        "cyan": "6",
        "white": "7",
        "gray": "8",  # bright black
        "bright_red": "9",
        "bright_green": "10",
        "bright_yellow": "11",
        "bright_blue": "12",
        "bright_purple": "13",
        "bright_cyan": "14",
        "bright_white": "15",
    }

    def __init__(self, theme_name: str = "modern", style: str = "arrow"):
        """初始化渲染器。

        Args:
            theme_name: 主题名称
            style: 分隔符样式 (arrow/round/slant/curve/none)
        """
        self._theme_loader = ThemeLoader()
        self._theme = self._theme_loader.load(theme_name)
        self._style = style
        self._separator = self.SEPARATORS.get(style, self.SEPARATORS["arrow"])
        self._separator_thin = self.SEPARATORS.get(f"{style}_thin", self._separator)

    def set_theme(self, theme_name: str) -> None:
        """设置主题。

        Args:
            theme_name: 主题名称
        """
        self._theme = self._theme_loader.load(theme_name)

    def set_style(self, style: str) -> None:
        """设置分隔符样式。

        Args:
            style: 分隔符样式
        """
        self._style = style
        self._separator = self.SEPARATORS.get(style, self.SEPARATORS["arrow"])
        self._separator_thin = self.SEPARATORS.get(f"{style}_thin", self._separator)

    def _hex_to_ansi(self, hex_color: str) -> str:
        """将十六进制颜色转换为 ANSI 256 色。

        Args:
            hex_color: 十六进制颜色代码 (#RRGGBB)

        Returns:
            ANSI 颜色代码
        """
        if not hex_color.startswith("#"):
            return self.COLOR_MAP.get(hex_color, "7")

        # 移除 # 前缀
        hex_color = hex_color.lstrip("#")

        # 转换为 RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # 计算 ANSI 256 色
        # 灰度范围
        if r == g == b:
            if r < 8:
                return "16"
            if r > 248:
                return "231"
            return str(((r - 8) // 10) + 232)

        # 216 色立方体
        r = r // 51
        g = g // 51
        b = b // 51
        return str(16 + (36 * r) + (6 * g) + b)

    def _get_color(self, color_name: str, default: str = "white") -> str:
        """获取颜色代码。

        Args:
            color_name: 颜色名称
            default: 默认颜色

        Returns:
            ANSI 颜色代码
        """
        colors = self._theme.get("colors", {})
        hex_color = colors.get(color_name, colors.get(default, "#ffffff"))
        return self._hex_to_ansi(hex_color)

    def _create_segments(
        self, outputs: list[ModuleOutput], color_cycle: Optional[list[str]] = None
    ) -> list[PowerlineSegment]:
        """创建 Powerline 分段。

        Args:
            outputs: 模块输出列表
            color_cycle: 背景色循环列表

        Returns:
            分段列表
        """
        if color_cycle is None:
            # 默认颜色循环
            color_cycle = ["primary", "info", "success", "warning", "accent"]

        segments = []
        colors = self._theme.get("colors", {})

        for i, output in enumerate(outputs):
            if not output.text:
                continue

            # 选择背景色
            bg_name = color_cycle[i % len(color_cycle)]
            bg_color = colors.get(bg_name, colors.get("primary", "#00d4aa"))

            # 根据状态选择前景色
            if output.status == ModuleStatus.ERROR:
                fg_name = "error"
            elif output.status == ModuleStatus.WARNING:
                fg_name = "warning"
            else:
                fg_name = "text"
            fg_color = colors.get(fg_name, colors.get("text", "#ffffff"))

            # 构建显示文本
            text = output.text
            if output.icon:
                text = f"{output.icon} {text}"

            segments.append(
                PowerlineSegment(
                    text=text,
                    bg_color=bg_color,
                    fg_color=fg_color,
                )
            )

        return segments

    def render_line(
        self,
        outputs: list[ModuleOutput],
        color_cycle: Optional[list[str]] = None,
        prefix: str = "",
        suffix: str = "",
    ) -> str:
        """渲染单行。

        Args:
            outputs: 模块输出列表
            color_cycle: 背景色循环列表
            prefix: 前缀字符串
            suffix: 后缀字符串

        Returns:
            渲染后的字符串
        """
        segments = self._create_segments(outputs, color_cycle)

        if not segments:
            return ""

        parts = []

        # 添加前缀
        if prefix:
            parts.append(prefix)

        # 渲染分段
        for i, segment in enumerate(segments):
            bg_code = self._hex_to_ansi(segment.bg_color)
            fg_code = self._hex_to_ansi(segment.fg_color)

            # 段内容
            content = f"\033[48;5;{bg_code}m\033[38;5;{fg_code}m {segment.text} \033[0m"
            parts.append(content)

            # 添加分隔符（除最后一个）
            if i < len(segments) - 1:
                next_bg = self._hex_to_ansi(segments[i + 1].bg_color)
                # 分隔符使用当前段的背景色作为前景色，下一段的背景色作为背景色
                sep = f"\033[48;5;{next_bg}m\033[38;5;{bg_code}m{self._separator}\033[0m"
                parts.append(sep)

        # 添加后缀
        if suffix:
            parts.append(suffix)

        return "".join(parts)

    def render_multi_line(
        self,
        lines: list[list[ModuleOutput]],
        color_cycles: Optional[list[list[str]]] = None,
    ) -> str:
        """渲染多行。

        Args:
            lines: 每行的模块输出列表
            color_cycles: 每行的颜色循环列表

        Returns:
            渲染后的多行字符串
        """
        if color_cycles is None:
            # 为每行使用不同的默认颜色循环
            color_cycles = [
                ["primary", "info"],  # 第一行：基础信息
                ["success", "warning"],  # 第二行：上下文和时间
                ["accent", "primary"],  # 第三行：成本统计
                ["info", "success"],  # 第四行：实时监控
            ]

        rendered_lines = []
        for i, line_outputs in enumerate(lines):
            if not line_outputs:
                continue

            cycle = color_cycles[i] if i < len(color_cycles) else None
            rendered = self.render_line(line_outputs, cycle)
            if rendered:
                rendered_lines.append(rendered)

        return "\n".join(rendered_lines)

    def render_preset_minimal(self, outputs: dict[str, ModuleOutput]) -> str:
        """渲染 minimal 预设。

        Args:
            outputs: 模块输出字典

        Returns:
            渲染后的字符串
        """
        # minimal 预设：dir, git_branch, model, cost_session, context_pct
        module_order = ["dir", "git_branch", "model", "cost_session", "context_pct"]
        line_outputs = []

        for name in module_order:
            if name in outputs:
                line_outputs.append(outputs[name])

        return self.render_line(line_outputs, ["primary", "info", "success"])

    def render_preset_standard(self, outputs: dict[str, ModuleOutput]) -> str:
        """渲染 standard 预设（3行）。

        Args:
            outputs: 模块输出字典

        Returns:
            渲染后的字符串
        """
        # 行1: dir, git_branch, model, version
        line1_modules = ["dir", "git_branch", "model", "version"]
        line1 = [outputs[m] for m in line1_modules if m in outputs]

        # 行2: context_bar, session_time, reset_timer
        line2_modules = ["context_bar", "session_time", "reset_timer"]
        line2 = [outputs[m] for m in line2_modules if m in outputs]

        # 行3: cost_session, cost_today, burn_rate
        line3_modules = ["cost_session", "cost_today", "burn_rate"]
        line3 = [outputs[m] for m in line3_modules if m in outputs]

        return self.render_multi_line([line1, line2, line3])

    def render_preset_full(self, outputs: dict[str, ModuleOutput]) -> str:
        """渲染 full 预设（4行）。

        Args:
            outputs: 模块输出字典

        Returns:
            渲染后的字符串
        """
        # 行1: 基础信息
        line1_modules = ["dir", "git_branch", "model", "plan", "version"]
        line1 = [outputs[m] for m in line1_modules if m in outputs]

        # 行2: 上下文和时间
        line2_modules = ["context_bar", "session_time", "reset_timer", "block_usage"]
        line2 = [outputs[m] for m in line2_modules if m in outputs]

        # 行3: 成本统计
        line3_modules = ["cost_session", "cost_today", "cost_week", "burn_rate"]
        line3 = [outputs[m] for m in line3_modules if m in outputs]

        # 行4: 实时监控
        line4_modules = ["mcp_status", "agent_status", "todo_progress"]
        line4 = [outputs[m] for m in line4_modules if m in outputs]

        return self.render_multi_line([line1, line2, line3, line4])


class PowerlineLayout:
    """Powerline 布局管理器。

    管理不同预设的模块布局。
    """

    # 预设配置
    PRESETS = {
        "minimal": {
            "lines": [
                ["dir", "git_branch", "model", "cost_session", "context_pct"],
            ],
            "color_cycles": [
                ["primary", "info", "success"],
            ],
        },
        "standard": {
            "lines": [
                ["dir", "git_branch", "model", "version"],
                ["context_bar", "session_time", "reset_timer"],
                ["cost_session", "cost_today", "burn_rate"],
            ],
            "color_cycles": [
                ["primary", "info"],
                ["success", "warning"],
                ["accent", "primary"],
            ],
        },
        "full": {
            "lines": [
                ["dir", "git_branch", "model", "plan", "version"],
                ["context_bar", "session_time", "reset_timer", "block_usage"],
                ["cost_session", "cost_today", "cost_week", "burn_rate"],
                ["mcp_status", "agent_status", "todo_progress"],
            ],
            "color_cycles": [
                ["primary", "info", "success"],
                ["success", "warning", "accent"],
                ["accent", "primary", "info"],
                ["info", "success"],
            ],
        },
    }

    @classmethod
    def get_preset_names(cls) -> list[str]:
        """获取所有预设名称。

        Returns:
            预设名称列表
        """
        return list(cls.PRESETS.keys())

    @classmethod
    def get_preset(cls, name: str) -> dict[str, Any]:
        """获取预设配置。

        Args:
            name: 预设名称

        Returns:
            预设配置
        """
        return cls.PRESETS.get(name, cls.PRESETS["standard"])

    @classmethod
    def render_preset(
        cls, preset_name: str, outputs: dict[str, ModuleOutput], renderer: PowerlineRenderer
    ) -> str:
        """渲染预设布局。

        Args:
            preset_name: 预设名称
            outputs: 模块输出字典
            renderer: Powerline 渲染器

        Returns:
            渲染后的字符串
        """
        preset = cls.get_preset(preset_name)
        lines = preset["lines"]
        color_cycles = preset["color_cycles"]

        # 构建每行的输出列表
        line_outputs = []
        for line_modules in lines:
            line = []
            for module_name in line_modules:
                if module_name in outputs:
                    output = outputs[module_name]
                    # 跳过禁用的模块
                    if output.status != ModuleStatus.DISABLED:
                        line.append(output)
            if line:
                line_outputs.append(line)

        return renderer.render_multi_line(line_outputs, color_cycles)
