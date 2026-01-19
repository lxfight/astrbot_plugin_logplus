# 📝 AstrBot LogPlus - 日志增强插件

> 为 AstrBot 提供完整的日志持久化解决方案，让问题排查更简单！

AstrBot 默认仅将日志输出到控制台，不保存到文件。当出现问题需要排查时，往往因为日志丢失而难以复现和定位问题。

本插件提供**日志持久化**、**分类存储**、**自动压缩**、**一键发送**等功能，帮助开发者和用户更好地管理和分享日志。

---

## 🎯 为什么需要这个插件？

### 👨‍💻 开发者视角
- **🔍 问题排查** - 保留完整历史日志，定位问题根源不再靠猜
- **🐛 插件调试** - 独立的插件日志目录，调试时不被其他日志干扰
- **⚠️ 错误监控** - 单独的错误日志文件，快速发现系统异常
- **📊 日志审计** - 支持导出和归档，满足合规和分析需求

### 👥 用户反馈场景
- **🆘 萌新快速反馈**
  遇到错误时，只需一条命令 `/logplus send errors` 就能把错误日志发给开发者，不用翻找文件夹！

- **🎯 精准问题上报**
  某个插件出问题？用 `/logplus send plugin 插件名` 精准发送该插件日志给开发者

- **📦 完整日志提供**
  开发者需要完整日志？`/logplus send all` 一键打包所有日志并发送

- **💡 降低技术门槛**
  不懂技术的用户也能通过简单命令提供有效日志，帮助 AstrBot 和插件开发者快速修复问题

- **🔧 远程协助调试**
  支持团队通过聊天平台直接接收日志文件，无需教用户怎么找文件、怎么上传

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📁 **日志持久化** | 自动将所有日志保存到文件，永久保留 |
| 📂 **分类存储** | 按 Core/插件/错误 分别存储，快速定位问题源 |
| 🔄 **日志轮换** | 支持按大小或时间自动切割，避免单文件过大 |
| 🗜️ **自动压缩** | 旧日志自动压缩为 .gz 格式，节省 50%+ 磁盘空间 |
| 🧹 **自动清理** | 按天数或总大小自动清理过期日志，避免占满磁盘 |
| 🔒 **敏感脱敏** | 自动隐藏 token/password 等敏感信息，保护隐私 |
| 🔍 **日志搜索** | 支持关键词搜索，快速定位问题相关日志 |
| 📤 **一键发送** | 打包日志为 zip 并直接发送，无需手动操作 |

---

## 🎮 命令列表

### 📊 查看与搜索
```bash
/logplus status              # 查看日志状态（文件数、大小、时间范围等）
/logplus search <关键词>     # 搜索日志内容，快速定位问题
```

### 📤 发送日志（推荐）
```bash
/logplus send all            # 发送全部日志文件（自动打包为 zip）
/logplus send errors         # 发送错误日志文件（仅 ERROR 级别）
/logplus send plugin <名>    # 发送指定插件日志（支持模糊匹配）
```

### 🛠️ 管理操作
```bash
/logplus export [天数]       # 导出最近 N 天日志到本地（默认 7 天）
/logplus clean              # 手动清理旧日志
/logplus help               # 显示帮助信息
```

---

## 📁 日志目录结构

```
{插件数据目录}/
├── all/                    # 全局日志（所有日志汇总）
│   ├── all.log
│   └── all.log.1.gz        # 自动压缩的历史日志
├── core/                   # AstrBot 核心日志
│   └── core.log
├── errors/                 # 错误日志（ERROR 及以上级别）
│   └── error.log
├── plugins/                # 按插件分类
│   ├── astrbot_plugin_xxx/
│   │   └── plugin.log
│   └── astrbot_plugin_yyy/
│       └── plugin.log
└── exports/                # 导出/发送生成的 zip 包
    ├── all_logs_20260119_143052.zip
    └── error_logs_20260119_143125.zip
```

---

## ⚙️ 配置项

<details>
<summary>点击展开配置说明（默认配置已经够用，高级用户可按需调整）</summary>

### 日志级别与轮换
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `log_level` | string | `DEBUG` | 全局最低记录级别 |
| `max_file_size_mb` | int | `10` | 单个日志文件最大大小（MB） |
| `backup_count` | int | `5` | 保留轮换文件数量 |
| `rotation_strategy` | string | `size` | 轮换策略：size/time/hybrid |
| `rotation_interval` | string | `daily` | 时间轮换间隔：hourly/daily |

### 功能开关
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_all_log` | bool | `true` | 保存全局日志（all.log） |
| `enable_core_log` | bool | `true` | 保存 Core 日志 |
| `enable_error_log` | bool | `true` | 单独保存错误日志 |
| `enable_plugin_separation` | bool | `true` | 按插件分类存储 |

### 压缩与清理
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_compression` | bool | `true` | 自动压缩旧日志为 .gz |
| `compression_after_days` | int | `1` | N 天后压缩 |
| `auto_clean_enabled` | bool | `true` | 启用自动清理旧日志 |
| `max_total_size_mb` | int | `500` | 日志总大小上限（MB） |
| `max_age_days` | int | `30` | 最大保留天数 |

### 隐私保护
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_sensitive_filter` | bool | `true` | 启用敏感信息脱敏 |
| `sensitive_keywords` | string | `token,password,...` | 敏感关键词（逗号分隔） |

</details>

---

## 💡 使用示例

### 场景 1：用户遇到错误想反馈
```bash
用户：插件报错了，怎么办？
管理员：发一下错误日志吧
用户：/logplus send errors
# 自动打包并发送错误日志 zip 文件
```

### 场景 2：开发者调试插件问题
```bash
开发者：你的 livingmemory 插件报错了，发下日志
用户：/logplus send plugin living
# 模糊匹配插件名，自动打包 astrbot_plugin_livingmemory 的日志
```

### 场景 3：排查复杂问题需要完整日志
```bash
开发者：这个问题比较复杂，需要看完整日志
用户：/logplus send all
# 打包所有日志（all/core/errors/plugins）发送
```

---

## 🔧 技术细节

- **非阻塞写入** - 每条日志写入后立即 flush，确保实时性且不影响主进程性能
- **异步压缩** - 使用线程池异步压缩日志，不阻塞日志写入
- **智能匹配** - 插件名支持模糊匹配，未匹配或多匹配时自动列出候选项
- **自动清理** - 后台定时任务自动清理过期日志，支持按大小和时间双重限制

---

## 📄 许可证

GNU Affero General Public License v3.0 (AGPL-3.0)

---

## 🔗 相关链接

- [AstrBot 项目主页](https://github.com/AstrBotDevs/AstrBot)
- [问题反馈](https://github.com/lxfight/astrbot_plugin_logplus/issues)
