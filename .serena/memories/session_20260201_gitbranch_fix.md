# GitBranchModule 修复 + 无效模块清理 - 2026-02-01

## 修复的问题

### 1. git_branch 模块不显示
**根因分析**:
- `GitBranchModule.is_available()` 依赖 `self._is_git_repo`
- `_is_git_repo` 只在 `refresh()` 方法中被设置
- 但 `StatuslineEngine.initialize()` 在调用 `is_available()` 前没有调用 `refresh()`
- 结果：模块初始化时 `_is_git_repo = False`，导致被跳过

**修复方案**:
```python
# src/cc_statusline/modules/basic.py:122-124
def initialize(self) -> None:
    """初始化模块。"""
    self.refresh()  # 初始化时获取分支信息
```

### 2. block_usage 和 cost_week 模块不显示
**根因分析**:
- `BlockUsageModule` 依赖 `cost.block_start_time` ��段
- `CostWeekModule` 依赖 `cost.weekly_cost` 字段
- **Claude Code API 不提供这些字段！**

**Claude Code StatusLine API 实际提供的字段**:
```json
{
  "cost": {
    "total_cost_usd": 0.01234,
    "total_duration_ms": 45000,
    "total_api_duration_ms": 2300,
    "total_lines_added": 156,
    "total_lines_removed": 23
  },
  "context_window": {
    "used_percentage": 42.5,
    "remaining_percentage": 57.5,
    "total_input_tokens": 15234,
    "total_output_tokens": 4521
  }
}
```

**修复方案**: 删除这两个模块

## 修改的文件

1. `src/cc_statusline/modules/basic.py`
   - GitBranchModule.initialize() 添加 `self.refresh()` 调用

2. `src/cc_statusline/modules/time_modules.py`
   - 删除 BlockUsageModule 类（约120行）
   - 更新 _register_modules() 移除注册

3. `src/cc_statusline/modules/cost.py`
   - 删除 CostWeekModule 类（约75行）
   - 更新 _register_modules() 移除注册

4. `src/cc_statusline/render/powerline.py`
   - render_preset_full() 移除 block_usage, cost_week
   - PowerlineLayout.PRESETS["full"] 移除相关模块

## 修复后的 full 预设

```
第1行: dir, git_branch, model, version
第2行: context_bar, session_time, reset_timer
第3行: cost_session, cost_today, burn_rate
第4行: mcp_status, agent_status, todo_progress
```

## 验证结果

- ✅ 268 个测试全部通过
- ✅ git_branch 正确显示分支名
- ✅ 无 block_usage/cost_week 引用残留
- ✅ grep 验证无遗漏

## 技术要点

1. **不依赖上下文的模块**（如 git_branch）需要在 `initialize()` 中主动获取数据
2. **依赖上下文的模块**（如 model, cost_*）在 `set_context()` 后自动更新
3. **模块删除流程**：删除类 → 删除注册 → 删除预设引用 → grep 验证
