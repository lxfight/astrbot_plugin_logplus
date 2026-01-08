# AstrBot LogPlus 日志增强插件

AstrBot 默认仅将日志输出到控制台，不保存到文件。当出现问题需要排查时，往往因为日志丢失而难以复现和定位问题。

本插件为 AstrBot 提供完整的日志持久化方案，支持按插件分类存储、自动轮换、压缩归档等功能。

## 功能特性

- **日志持久化** - 自动将所有日志保存到文件
- **分类存储** - 按 Core/插件/错误 分别存储，便于定位问题
- **日志轮换** - 支持按大小或时间自动切割，避免单文件过大
- **自动压缩** - 旧日志自动压缩为 .gz 格式，节省磁盘空间
- **自动清理** - 按天数或总大小自动清理过期日志
- **敏感脱敏** - 自动隐藏 token/password 等敏感信息
- **日志搜索** - 支持关键词搜索，快速定位问题
- **日志导出** - 一键导出指定时间段日志

## 日志目录结构

```
{插件数据目录}/
├── all/                    # 全局日志（所有日志汇总）
│   └── all.log
├── core/                   # AstrBot 核心日志
│   └── core.log
├── errors/                 # 错误日志（ERROR及以上级别）
│   └── error.log
├── plugins/                # 按插件分类
│   ├── astrbot_plugin_xxx/
│   │   └── plugin.log
│   └── astrbot_plugin_yyy/
│       └── plugin.log
└── exports/                # 导出的日志压缩包
```

## 命令

| 命令 | 说明 |
|------|------|
| `/logplus status` | 查看日志状态（文件数、大小、时间范围等） |
| `/logplus search <关键词>` | 搜索日志内容 |
| `/logplus clean` | 手动清理旧日志 |
| `/logplus export [天数]` | 导出最近N天日志（默认7天） |
| `/logplus help` | 显示帮助信息 |

## 配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `log_level` | string | DEBUG | 最低记录级别 |
| `max_file_size_mb` | int | 10 | 单文件最大大小(MB) |
| `backup_count` | int | 5 | 保留轮换文件数量 |
| `rotation_strategy` | string | size | 轮换策略: size/time/hybrid |
| `rotation_interval` | string | daily | 时间轮换间隔: hourly/daily |
| `enable_all_log` | bool | true | 保存全局日志 |
| `enable_core_log` | bool | true | 保存Core日志 |
| `enable_error_log` | bool | true | 单独保存错误日志 |
| `enable_plugin_separation` | bool | true | 按插件分类存储 |
| `enable_compression` | bool | true | 自动压缩旧日志 |
| `compression_after_days` | int | 1 | N天后压缩 |
| `auto_clean_enabled` | bool | true | 自动清理 |
| `max_total_size_mb` | int | 500 | 日志总大小上限(MB) |
| `max_age_days` | int | 30 | 最大保留天数 |
| `enable_sensitive_filter` | bool | true | 敏感信息脱敏 |
| `sensitive_keywords` | string | token,password,... | 敏感关键词(逗号分隔) |

## 使用场景

1. **问题排查** - 出现异常时查看历史日志，定位问题根源
2. **插件调试** - 查看特定插件的独立日志，不受其他日志干扰
3. **错误监控** - 通过错误日志快速发现系统异常
4. **日志审计** - 导出日志用于分析和存档

## 许可证

GNU Affero General Public License v3.0 (AGPL-3.0)
