"""主题加载器。

提供主题的加载、解析和管理功能。
"""

from pathlib import Path
from typing import Any, Optional

import yaml

from cc_status.theme.builtins import BUILTIN_THEMES


class ThemeLoader:
    """主题加载器。

    从文件或内置主题加载主题配置。
    """

    def __init__(self, theme_paths: Optional[list[Path]] = None) -> None:
        """初始化主题加载器。

        Args:
            theme_paths: 主题文件搜索路径列表
        """
        self._theme_paths = theme_paths or self._get_default_paths()
        self._cache: dict[str, dict[str, Any]] = {}

    def _get_default_paths(self) -> list[Path]:
        """获取默认主题搜索路径。

        Returns:
            路径列表
        """
        return [
            Path.cwd() / "themes",  # 项目 themes 目录
            Path.home() / ".claude" / "themes",  # 用户主题目录
            Path(__file__).parent.parent.parent / "themes",  # 包内 themes 目录
        ]

    def _find_theme_file(self, name: str) -> Optional[Path]:
        """查找主题文件。

        Args:
            name: 主题名称

        Returns:
            主题文件路径
        """
        # 支持直接路径
        path = Path(name)
        if path.exists():
            return path

        # 查找 .yaml 后缀
        for base_path in self._theme_paths:
            theme_file = base_path / f"{name}.yaml"
            if theme_file.exists():
                return theme_file

        return None

    def load(self, name: str) -> dict[str, Any]:
        """加载主题。

        Args:
            name: 主题名称

        Returns:
            主题配置字典

        Raises:
            FileNotFoundError: 主题未找到
        """
        # 检查缓存
        if name in self._cache:
            return self._cache[name].copy()

        # 尝试加载内置主题
        if name in BUILTIN_THEMES:
            theme_config = BUILTIN_THEMES[name]
            self._cache[name] = theme_config
            return theme_config.copy()

        # 尝试从文件加载
        theme_file = self._find_theme_file(name)
        if theme_file is None:
            raise FileNotFoundError(f"主题 '{name}' 未找到")

        theme_config = self._load_from_file(theme_file)
        self._cache[name] = theme_config
        return theme_config.copy()

    def _load_from_file(self, path: Path) -> dict[str, Any]:
        """从文件加载主题配置。

        Args:
            path: 主题文件路径

        Returns:
            主题配置字典
        """
        with open(path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # 应用默认值
        config = self._apply_defaults(config)
        return config

    def _apply_defaults(self, config: dict[str, Any]) -> dict[str, Any]:
        """应用默认配置。

        Args:
            config: 原始配置

        Returns:
            合并后的配置
        """
        defaults = {
            "name": config.get("name", "Unknown"),
            "description": config.get("description", ""),
            "colors": {
                "primary": "#00d4aa",
                "success": "#4ade80",
                "warning": "#fbbf24",
                "error": "#ef4444",
                "info": "#3b82f6",
                "text": "#ffffff",
                "background": "#1e1e2e",
                "dim": "#a0a0a0",
            },
            "icons": {
                "mcp": "🔌",
                "mcp_running": "🟢",
                "mcp_error": "🔴",
                "mcp_warning": "🟡",
                "time": "⏱️",
                "git": "📦",
                "system": "🖥️",
                "stats": "📊",
                "separator": " │ ",
            },
            "styles": {
                "module": {
                    "separator": " │ ",
                    "prefix": "",
                    "suffix": "",
                },
                "container": {
                    "padding": " ",
                    "border": "",
                },
            },
            "fonts": {
                "bold": True,
                "italic": False,
            },
        }

        # 递归合并颜色
        if "colors" in config:
            defaults["colors"].update(config["colors"])
        config["colors"] = defaults["colors"]

        # 合并图标配置
        if "icons" in config:
            defaults["icons"].update(config["icons"])
        config["icons"] = defaults["icons"]

        # 合并样式配置
        if "styles" in config:
            defaults["styles"].update(config["styles"])
        config["styles"] = defaults["styles"]

        # 合并字体配置
        if "fonts" in config:
            defaults["fonts"].update(config["fonts"])
        config["fonts"] = defaults["fonts"]

        # 更新名称和描述
        if "name" not in config:
            config["name"] = defaults["name"]
        if "description" not in config:
            config["description"] = defaults["description"]

        return config

    def list_available(self) -> list[str]:
        """列出所有可用的主题。

        Returns:
            主题名称列表
        """
        themes: set[str] = set()

        # 添加内置主题
        themes.update(BUILTIN_THEMES.keys())

        # 扫描文件主题
        for base_path in self._theme_paths:
            if base_path.exists():
                for f in base_path.glob("*.yaml"):
                    themes.add(f.stem)

        return sorted(themes)

    def is_valid(self, name: str) -> bool:
        """检查主题是否有效。

        Args:
            name: 主题名称

        Returns:
            是否有效
        """
        try:
            self.load(name)
            return True
        except (FileNotFoundError, yaml.YAMLError):
            return False

    def get_color(self, theme_name: str, color_key: str) -> str:
        """获取主题颜色。

        Args:
            theme_name: 主题名称
            color_key: 颜色键

        Returns:
            颜色值
        """
        theme = self.load(theme_name)
        colors = theme.get("colors", {})
        return str(colors.get(color_key, ""))

    def get_icon(self, theme_name: str, icon_key: str) -> str:
        """获取主题图标。

        Args:
            theme_name: 主题名称
            icon_key: 图标键

        Returns:
            图标
        """
        theme = self.load(theme_name)
        icons = theme.get("icons", {})
        return str(icons.get(icon_key, ""))

    def clear_cache(self) -> None:
        """清除缓存。"""
        self._cache.clear()

    def reload(self, name: str) -> dict[str, Any]:
        """重新加载主题（清除缓存后加载）。

        Args:
            name: 主题名称

        Returns:
            主题配置字典
        """
        if name in self._cache:
            del self._cache[name]
        return self.load(name)


# 全局加载器实例
theme_loader = ThemeLoader()
