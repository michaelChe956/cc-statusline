"""模块基类定义。

提供所有功能模块的基类和数据类型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ModuleStatus(Enum):
    """模块状态枚举。"""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ModuleOutput:
    """模块输出数据类。

    Attributes:
        text: 显示的文本内容
        icon: 显示的图标（可选）
        color: 颜色标识（可选）
        status: 模块状态（可选）
        tooltip: 悬停提示信息（可选）
        style: 自定义样式（可选）
    """

    text: str
    icon: str = ""
    color: str = ""
    status: ModuleStatus = ModuleStatus.SUCCESS
    tooltip: str = ""
    style: str = ""

    def __str__(self) -> str:
        """返回格式化后的输出。"""
        parts = []
        if self.icon:
            parts.append(self.icon)
        parts.append(self.text)
        return " ".join(parts)

    def to_dict(self) -> dict:
        """转换为字典格式。"""
        return {
            "text": self.text,
            "icon": self.icon,
            "color": self.color,
            "status": self.status.value,
            "tooltip": self.tooltip,
            "style": self.style,
        }


@dataclass
class ModuleMetadata:
    """模块元数据。

    Attributes:
        name: 模块名称
        description: 模块描述
        version: 模块版本
        author: 模块作者
        enabled: 是否默认启用
    """

    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    enabled: bool = True
    dependencies: list[str] = field(default_factory=list)


@runtime_checkable
class BaseModule(Protocol):
    """功能模块协议基类。

    所有功能模块必须实现此协议。
    """

    @property
    def metadata(self) -> ModuleMetadata:
        """获取模块元数据。"""
        ...

    def initialize(self) -> None:
        """初始化模块。

        在模块首次加载时调用，用于设置和初始化。
        """
        pass

    def refresh(self) -> None:
        """刷新模块数据。

        在每次更新周期开始时调用，用于获取最新数据。
        """
        pass

    def get_output(self) -> ModuleOutput:
        """获取模块输出。

        Returns:
            ModuleOutput: 模块的输出数据
        """
        ...

    def cleanup(self) -> None:
        """清理资源。

        在模块卸载时调用，用于释放资源。
        """
        pass

    def is_available(self) -> bool:
        """检查模块是否可用。

        Returns:
            bool: 模块是否可用
        """
        return True

    def get_refresh_interval(self) -> float:
        """获取刷新间隔（秒）。

        Returns:
            float: 刷新间隔时间
        """
        return 1.0

    def set_context(self, context: dict[str, Any]) -> None:
        """设置上下文数据。

        从 Claude Code statusLine hook 接收的 JSON 数据。

        Args:
            context: 包含 cost.total_duration_ms 等字段的字典
        """
        pass


class ModuleError(Exception):
    """模块相关错误。"""

    pass


class ModuleNotFoundError(ModuleError):
    """模块未找到错误。"""

    pass


class ModuleLoadError(ModuleError):
    """模块加载错误。"""

    pass
