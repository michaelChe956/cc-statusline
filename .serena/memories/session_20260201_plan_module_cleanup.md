# PlanModule 引用清理 - 2026-02-01

## 会话任务

清理代码库中对已删除 `PlanModule` 的所有引用，避免配置错误。

## 背景

虽然 `PlanModule` 类已在之前被删除，但代码中仍有 3 处引用了 `"plan"` 模块，导致配置错误。

## 完成的修改

### 1. commands.py 预设配置
**文件**: `src/cc_statusline/cli/commands.py`
**行号**: 488

```diff
- "full": ["dir", "git_branch", "model", "plan", "version", "context_bar", ...]
+ "full": ["dir", "git_branch", "model", "version", "context_bar", ...]
```

### 2. powerline.py 渲染方法
**文件**: `src/cc_statusline/render/powerline.py`
**行号**: 331

```diff
- line1_modules = ["dir", "git_branch", "model", "plan", "version"]
+ line1_modules = ["dir", "git_branch", "model", "version"]
```

### 3. PowerlineLayout 预设配置
**文件**: `src/cc_statusline/render/powerline.py`
**行号**: 379

```diff
- ["dir", "git_branch", "model", "plan", "version"],
+ ["dir", "git_branch", "model", "version"],
```

## 验证结果

### 代码搜索验证
✅ 无 `PlanModule` 类引用
✅ 无 `"plan"` 模块字符串引用（双引号）
✅ 无 `'plan'` 模块字符串引用（单引号）

### 功能测试
✅ `full` 预设正常渲染，无错误
✅ 可用模块总数：24个
✅ `plan` 模块不在可用模块列表中
✅ `context_bar` 模块已正确注册并启用

### 模块注册验证
```bash
包含 context 或 plan 的模块:
  - context_bar          enabled=True
  - context_pct          enabled=True
```

## context_bar 模块状态

### 用户反馈
用户报告 "context_bar 丢了"

### 调查结果
经过全面检查，`context_bar` 模块**没有丢失**：

1. ✅ **模块注册**：已正确注册并启用
2. ✅ **配置位置**：仍在 `preset_modules["full"]` 和 `PowerlineLayout.PRESETS["full"]` 的第二行
3. ✅ **功能测试**：在有上下文数据时正常工作
   - 无上下文：不显示（预期行为）
   - 有上下文（26%）：显示 `[██░░░░░░░░] 26%`
   - 有上下文（80%）：显示 `[████████░░] 80%` (WARNING)

### 工作原理
`context_bar` 模块需要**上下文数据**才能显示：
- 在命令行测试（`cc-statusline --once`）时没有上下文数据，所以不显示 ✓
- 在实际 Claude Code 环境中，如果收到上下文数据（`context_window.used_percentage`），会正常显示 ✓

### 代码逻辑
```python
def is_available(self) -> bool:
    """检查模块是否可用。"""
    return self._percentage > 0  # 只有百分比大于0时才可用
```

## 影响范围

- **修改文件**: 2个（`commands.py`, `powerline.py`）
- **影响功能**: `full` 预设不再包含订阅计划显示
- **向后兼容**: 用户配置中的 `"plan"` 模块名将被自动忽略（不在注册表中）

## 当前状态栏内容

### full 预设包含的模块（11个）

**第一行 - 基础信息**:
- `dir` - 📁 目录路径
- `git_branch` - 🌿 Git分支
- `model` - 🤖 模型名称
- `version` - 📦 版本号

**第二行 - 上下文和时间**:
- `context_bar` - 🧠 上下文使用进度条
- `session_time` - ⏱️ 会话时间
- `reset_timer` - 🔄 重置计时器
- `block_usage` - ⏰ 5小时窗口使用

**第三行 - 成本统计**:
- `cost_session` - 💰 会话成本
- `cost_today` - 📅 今日成本
- `cost_week` - 📊 本周成本
- `burn_rate` - 🔥 燃烧率

**第四行 - 实时监控**:
- `mcp_status` - 🟢 MCP状态
- `agent_status` - 🤖 代理状态
- `todo_progress` - 📝 TODO进度

**总计**: 18个已实现模块，full 预设显示 15个模块，**功能完整**。

## 技术要点

1. **模块删除流程**: 删除模块类时，必须同时清理所有配置引用
2. **可用性检查**: `is_available()` 决定模块是否显示，需要确保逻辑正确
3. **上下文依赖**: 依赖上下文数据的模块在无数据时会自动隐藏
4. **验证方法**: 使用 `grep -r "pattern"` 确保无遗漏引用

## 下一步

等待用户确认 `context_bar` 在实际 Claude Code 环境中的表现。如有问题，需要进一步调查上下文数据传递机制。
