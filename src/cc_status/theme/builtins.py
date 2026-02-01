"""内置主题配置。

提供多种预设主题配置。
"""

from typing import Any

BUILTIN_THEMES: dict[str, dict[str, Any]] = {
    "modern": {
        "name": "Modern",
        "description": "默认主题，现代简洁风格，青色主调",
        "colors": {
            "primary": "#00d4aa",
            "success": "#4ade80",
            "warning": "#fbbf24",
            "error": "#ef4444",
            "info": "#3b82f6",
            "text": "#ffffff",
            "background": "#1e1e2e",
            "dim": "#a0a0a0",
            "accent": "#22d3ee",
        },
        "icons": {
            "mcp": "🔌",
            "mcp_running": "🟢",
            "mcp_error": "🔴",
            "mcp_warning": "🟡",
            "time": "⏱️",
            "git": "📦",
            "git_branch": "⑂",
            "git_dirty": "✗",
            "system": "🖥️",
            "cpu": "⚡",
            "memory": "💾",
            "disk": "💿",
            "stats": "📊",
            "tokens": "🪙",
            "commands": "⌨️",
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
    },
    "minimal": {
        "name": "Minimal",
        "description": "极简风格，黑白配色",
        "colors": {
            "primary": "#ffffff",
            "success": "#ffffff",
            "warning": "#ffffff",
            "error": "#ffffff",
            "info": "#ffffff",
            "text": "#ffffff",
            "background": "#000000",
            "dim": "#666666",
            "accent": "#cccccc",
        },
        "icons": {
            "mcp": "M",
            "mcp_running": "●",
            "mcp_error": "×",
            "mcp_warning": "!",
            "time": "T",
            "git": "G",
            "system": "S",
            "stats": "S",
            "separator": " | ",
        },
        "styles": {
            "module": {
                "separator": " | ",
                "prefix": "[",
                "suffix": "]",
            },
            "container": {
                "padding": "",
                "border": "",
            },
        },
        "fonts": {
            "bold": False,
            "italic": False,
        },
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "description": "赛博朋克风格，霓虹色调",
        "colors": {
            "primary": "#ff00ff",
            "success": "#00ff00",
            "warning": "#ffff00",
            "error": "#ff0000",
            "info": "#00ffff",
            "text": "#e0e0e0",
            "background": "#0d0221",
            "dim": "#8080ff",
            "accent": "#ff0080",
        },
        "icons": {
            "mcp": "⚡",
            "mcp_running": "◉",
            "mcp_error": "◉",
            "mcp_warning": "◉",
            "time": "⏱",
            "git": "⎇",
            "git_branch": "⎇",
            "git_dirty": "⨯",
            "system": "💻",
            "cpu": "⚡",
            "memory": "◉",
            "disk": "💿",
            "stats": "▣",
            "tokens": "◈",
            "commands": "⌨",
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
                "border": "━",
            },
        },
        "fonts": {
            "bold": True,
            "italic": False,
        },
    },
    "catppuccin": {
        "name": "Catppuccin",
        "description": "柔和主题，温暖色调",
        "colors": {
            "primary": "#cba6f7",
            "success": "#a6e3a1",
            "warning": "#f9e2af",
            "error": "#f38ba8",
            "info": "#89b4fa",
            "text": "#cdd6f4",
            "background": "#1e1e2e",
            "dim": "#a6adc8",
            "accent": "#f5c2e7",
        },
        "icons": {
            "mcp": "🔌",
            "mcp_running": "●",
            "mcp_error": "✕",
            "mcp_warning": "!",
            "time": "⏱",
            "git": "⎇",
            "git_branch": "⎇",
            "git_dirty": "✎",
            "system": "🖥",
            "cpu": "⚙",
            "memory": "💾",
            "disk": "💿",
            "stats": "📊",
            "tokens": "◈",
            "commands": "⌨",
            "separator": "  ",
        },
        "styles": {
            "module": {
                "separator": "  ",
                "prefix": "",
                "suffix": "",
            },
            "container": {
                "padding": "  ",
                "border": "",
            },
        },
        "fonts": {
            "bold": True,
            "italic": False,
        },
    },
    "nord": {
        "name": "Nord",
        "description": "冷色调主题，北极风格",
        "colors": {
            "primary": "#88c0d0",
            "success": "#a3be8c",
            "warning": "#ebcb8b",
            "error": "#bf616a",
            "info": "#5e81ac",
            "text": "#eceff4",
            "background": "#2e3440",
            "dim": "#81a1c1",
            "accent": "#8fbcbb",
        },
        "icons": {
            "mcp": "🔌",
            "mcp_running": "●",
            "mcp_error": "✕",
            "mcp_warning": "!",
            "time": "⏱",
            "git": "⎇",
            "git_branch": "⎇",
            "git_dirty": "±",
            "system": "🖥",
            "cpu": "⚙",
            "memory": "💾",
            "disk": "💿",
            "stats": "📊",
            "tokens": "◈",
            "commands": "⌨",
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
    },
    "dracula": {
        "name": "Dracula",
        "description": "深色主题，紫色调",
        "colors": {
            "primary": "#bd93f9",
            "success": "#50fa7b",
            "warning": "#f1fa8c",
            "error": "#ff5555",
            "info": "#8be9fd",
            "text": "#f8f8f2",
            "background": "#282a36",
            "dim": "#6272a4",
            "accent": "#ff79c6",
        },
        "icons": {
            "mcp": "⚡",
            "mcp_running": "●",
            "mcp_error": "✕",
            "mcp_warning": "!",
            "time": "⏱",
            "git": "⎇",
            "git_branch": "⎇",
            "git_dirty": "±",
            "system": "💻",
            "cpu": "⚙",
            "memory": "💾",
            "disk": "💿",
            "stats": "📊",
            "tokens": "◈",
            "commands": "⌨",
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
    },
    "gruvbox": {
        "name": "Gruvbox",
        "description": "复古主题，暖色调",
        "colors": {
            "primary": "#fabd2f",
            "success": "#b8bb26",
            "warning": "#fabd2f",
            "error": "#fb4934",
            "info": "#83a598",
            "text": "#ebdbb2",
            "background": "#282828",
            "dim": "#928374",
            "accent": "#fe8019",
        },
        "icons": {
            "mcp": "⚡",
            "mcp_running": "●",
            "mcp_error": "✕",
            "mcp_warning": "!",
            "time": "⏱",
            "git": "⎇",
            "git_branch": "⎇",
            "git_dirty": "±",
            "system": "💻",
            "cpu": "⚙",
            "memory": "💾",
            "disk": "💿",
            "stats": "📊",
            "tokens": "◈",
            "commands": "⌨",
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
    },
    "monokai": {
        "name": "Monokai",
        "description": "经典深色主题",
        "colors": {
            "primary": "#a6e22e",
            "success": "#a6e22e",
            "warning": "#fd971f",
            "error": "#f92672",
            "info": "#66d9ef",
            "text": "#f8f8f2",
            "background": "#272822",
            "dim": "#75715e",
            "accent": "#e6db74",
        },
        "icons": {
            "mcp": "⚡",
            "mcp_running": "●",
            "mcp_error": "✕",
            "mcp_warning": "!",
            "time": "⏱",
            "git": "⎇",
            "git_branch": "⎇",
            "git_dirty": "±",
            "system": "💻",
            "cpu": "⚙",
            "memory": "💾",
            "disk": "💿",
            "stats": "📊",
            "tokens": "◈",
            "commands": "⌨",
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
    },
}


def get_theme_names() -> list[str]:
    """获取所有内置主题名称。

    Returns:
        主题名称列表
    """
    return list(BUILTIN_THEMES.keys())


def get_default_theme() -> dict[str, Any]:
    """获取默认主题。

    Returns:
        默认主题配置
    """
    return BUILTIN_THEMES["modern"].copy()
