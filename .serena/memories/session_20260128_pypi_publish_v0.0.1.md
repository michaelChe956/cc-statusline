# cc-statusline PyPI 发布会话 - 2026-01-28

## 会话目标
发布 cc-statusline 到 PyPI（TestPyPI 测试）

## 遇到的问题和解决方案

### 问题 1：入口点配置错误
**现象**：
- `pyproject.toml` 配置：`cc-statusline = "cc_statusline.__main__:main"`
- 实际 `main()` 函数在 `cli/commands.py` 中
- TestPyPI 安装后显示可执行文件名为 `claude-statusline`

**解决方案**：
```toml
[project.scripts]
cc-statusline = "cc_statusline.cli.commands:main"
```

### 问题 2：CLI 中硬编码版本号
**现象**：
- `--version` 输出固定为 `0.2.0`
- 更新 `pyproject.toml` 版本号后 CLI 输出不变

**解决方案**：
```python
# cli/commands.py
from cc_statusline import __version__

parser.add_argument(
    "--version",
    action="version",
    version=f"%(prog)s {__version__}",
)
```

### 问题 3：版本号冲突和混乱
**现象**：
- TestPyPI 上有多个版本（0.2.0, 0.2.1, 0.2.2）
- uv 找不到最新版本
- 依赖版本在 TestPyPI 上不匹配

**解决方案**：
1. 重置版本号为 0.0.1（全新开始）
2. 手动删除 TestPyPI 上的旧版本
3. 使用 `--index-strategy unsafe-best-match` 解决依赖问题

### 问题 4：TestPyPI 索引延迟
**现象**：
- JSON API 显示最新版本存在
- Simple API（uv 使用）延迟更新
- 需要等待 5-30 分钟

**解决方案**：
- 等待索引更新
- 或使用 pip 代替 uv 测试
- 或从本地 wheel 直接安装验证

## 成功的发布流程

### 1. 版本号管理
```bash
# 修改版本号
# pyproject.toml
version = "0.0.1"

# src/cc_statusline/__init__.py
__version__ = "0.0.1"
```

### 2. 构建和验证
```bash
# 清理旧构建
rm -rf dist/ build/

# 构建
.venv/bin/python -m build

# 验证
.venv/bin/twine check dist/*
```

### 3. 上传到 TestPyPI
```bash
.venv/bin/twine upload --repository testpypi dist/*
```

### 4. 验证安装
```bash
uvx \
  --extra-index-url https://test.pypi.org/simple/ \
  --index-strategy unsafe-best-match \
  cc-statusline --version
```

## 创建的发布脚本

**位置**：`scripts/publish.sh`

**功能**：
- 自动清理、构建、验证、上传
- 支持 TestPyPI 和 PyPI 切换
- 彩色输出和错误处理
- 发布到正式 PyPI 前需要确认

**使用方法**：
```bash
./scripts/publish.sh          # TestPyPI（默认）
./scripts/publish.sh --prod   # 正式 PyPI
./scripts/publish.sh --help   # 查看帮助
```

## 关键配置文件

### pyproject.toml 关键配置
```toml
[project]
name = "cc-statusline"
version = "0.0.1"

[project.scripts]
cc-statusline = "cc_statusline.cli.commands:main"  # 正确的入口点

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### ~/.pypirc 配置模板
```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
username = __token__
password = <your-testpypi-token>

[pypi]
username = __token__
password = <your-pypi-token>
```

## 验证清单

发布前检查：
- [ ] 入口点配置正确（`cli.commands:main`）
- [ ] 版本号使用动态变量（`__version__`）
- [ ] pyproject.toml 和 __init__.py 版本号一致
- [ ] 构建产物通过 twine check
- [ ] 本地安装测试通过

TestPyPI 验证：
- [ ] 上传成功
- [ ] 删除旧版本（手动操作）
- [ ] 等待索引更新（5-30 分钟）
- [ ] 从 TestPyPI 安装测试通过
- [ ] `--version` 输出正确版本号
- [ ] 可执行文件名为 `cc-statusline`

## 最终状态

| 项目 | 值 |
|------|------|
| 包名 | cc-statusline |
| 版本 | 0.0.1 |
| 可执行文件 | cc-statusline ✅ |
| TestPyPI | ✅ 已发布并验证 |
| 正式 PyPI | ⏳ 待发布 |

## 下次会话建议

1. **发布到正式 PyPI**
   - 确认 0.0.1 功能完整
   - 使用 `./scripts/publish.sh --prod`
   - 版本号不可重复，谨慎操作

2. **版本号规划**
   - 0.0.x：开发版本
   - 0.1.0：第一个稳定版本
   - 遵循语义化版本规范

3. **文档更新**
   - README.md 添加 PyPI badge
   - 创建 CHANGELOG.md
   - 更新安装说明

## 技术决策记录

### 为什么使用 hatchling？
- 配置简单（`build-backend = "hatchling.build"`）
- 与现代 Python 打包标准兼容
- 无需额外配置即可正确处理入口点

### 为什么需要 build 包？
- `build` 提供 `python -m build` 命令（构建前端）
- `hatchling` 是构建后端（实际执行构建）
- 两者配合完成打包流程

### 为什么 TestPyPI 需要 --index-strategy unsafe-best-match？
- TestPyPI 只包含你的包，不包含依赖
- 需要从官方 PyPI 拉取依赖（httpx, psutil 等）
- unsafe-best-match 允许从多个索引查找最佳版本
