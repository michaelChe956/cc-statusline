"""模块包初始化。

导出所有模块相关类型。
"""

from cc_status.modules.base import (
    BaseModule,
    ModuleError,
    ModuleLoadError,
    ModuleMetadata,
    ModuleNotFoundError,
    ModuleOutput,
    ModuleStatus,
)
from cc_status.modules.registry import ModuleRegistry, registry

__all__ = [
    "ModuleStatus",
    "ModuleOutput",
    "ModuleMetadata",
    "BaseModule",
    "ModuleError",
    "ModuleNotFoundError",
    "ModuleLoadError",
    "ModuleRegistry",
    "registry",
]
