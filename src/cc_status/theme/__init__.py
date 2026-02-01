"""主题包初始化。

导出主题相关类型和工具。
"""

from cc_status.theme.builtins import BUILTIN_THEMES, get_default_theme, get_theme_names
from cc_status.theme.loader import ThemeLoader, theme_loader

__all__ = [
    "ThemeLoader",
    "theme_loader",
    "BUILTIN_THEMES",
    "get_theme_names",
    "get_default_theme",
]
