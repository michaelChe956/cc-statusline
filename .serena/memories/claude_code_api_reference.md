# Claude Code StatusLine API 完整字段映射

## API 版本
Claude Code v1.0+ (2026-02-01 验证)

## 传递方式
通过 **stdin** 以 JSON 格式传递给自定义 statusLine 命令

## 完整 JSON 结构

```json
{
  "hook_event_name": "Status",
  "session_id": "abc123...",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/current/working/directory",
  "model": {
    "id": "claude-opus-4-1",
    "display_name": "Opus"
  },
  "workspace": {
    "current_dir": "/current/working/directory",
    "project_dir": "/original/project/directory"
  },
  "version": "1.0.80",
  "output_style": {
    "name": "default"
  },
  "cost": {
    "total_cost_usd": 0.01234,
    "total_duration_ms": 45000,
    "total_api_duration_ms": 2300,
    "total_lines_added": 156,
    "total_lines_removed": 23
  },
  "context_window": {
    "total_input_tokens": 15234,
    "total_output_tokens": 4521,
    "context_window_size": 200000,
    "used_percentage": 42.5,
    "remaining_percentage": 57.5,
    "current_usage": {
      "input_tokens": 8500,
      "output_tokens": 1200,
      "cache_creation_input_tokens": 5000,
      "cache_read_input_tokens": 2000
    }
  }
}
```

## 字段映射表

### cost 对象

| 字段 | 类型 | cc-statusline 使用 | 说明 |
|------|------|-------------------|------|
| `total_cost_usd` | number | ✅ cost_session, cost_today, burn_rate | 累计总费用（美元） |
| `total_duration_ms` | number | ✅ session_time, burn_rate | 会话总时长（毫秒） |
| `total_api_duration_ms` | number | ❌ 未使用 | API 调用总时长 |
| `total_lines_added` | number | ❌ 未使用 | 累计添加代码行数 |
| `total_lines_removed` | number | ❌ 未使用 | 累计删除代码行数 |

### context_window 对象

| 字段 | 类型 | cc-statusline 使用 | 说明 |
|------|------|-------------------|------|
| `total_input_tokens` | number | ❌ 未使用 | 累计输入 token 数 |
| `total_output_tokens` | number | ❌ 未使用 | 累计输出 token 数 |
| `context_window_size` | number | ✅ context_pct, context_bar | 上下文窗口总大小 |
| `used_percentage` | number | ✅ context_pct, context_bar | 已使用百分比（0-100） |
| `remaining_percentage` | number | ❌ 未使用 | 剩余百分比 |
| `current_usage` | object/null | ❌ 未使用 | 当前 API 调用 token 使用 |

### model 对象

| 字段 | 类型 | cc-statusline 使用 | 说明 |
|------|------|-------------------|------|
| `id` | string | ✅ model | 模型 ID（claude-opus-4-1） |
| `display_name` | string | ✅ model | 模型显示名称（Opus） |

### 其他字段

| 字段 | 类型 | cc-statusline 使用 | 说明 |
|------|------|-------------------|------|
| `hook_event_name` | string | ❌ | 事件名称（固定 "Status"） |
| `session_id` | string | ❌ | 会话 ID |
| `transcript_path` | string | ❌ | 会话记录文件路径 |
| `cwd` | string | ✅ dir | 当前工作目录 |
| `version` | string | ✅ version | Claude Code 版本号 |
| `workspace.current_dir` | string | ❌ | 当前工作目录 |
| `workspace.project_dir` | string | ❌ | 项目根目录 |
| `output_style.name` | string | ❌ | 输出样式名称 |

## 不存在的字段（导致模块删除）

| 假设字段 | 期望用途 | 实际情况 |
|---------|---------|---------|
| `cost.block_start_time` | BlockUsageModule 计费窗口起始时间 | ❌ 不存在 |
| `cost.weekly_cost` | CostWeekModule 本周累计成本 | ❌ 不存在 |

## 未使用但可用的字段（潜在功能）

| 字段 | 潜在模块 | 价值 |
|------|---------|------|
| `total_lines_added/removed` | CodeChangesModule | 代码变更统计 |
| `total_api_duration_ms` | ApiLatencyModule | API 延迟监控 |
| `total_input/output_tokens` | TokenStatsModule | Token 使用统计 |

## 数据来源验证

- 📚 官方文档：https://code.claude.com/docs/en/statusline.md
- 🔍 验证方法：使用 Task tool (claude-code-guide agent)
- 📅 验证日期：2026-02-01
