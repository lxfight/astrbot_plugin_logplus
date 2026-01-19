import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .log_cleaner import LogCleaner


class CommandHandler:
    """命令处理器"""

    def __init__(self, data_dir: Path, cleaner: "LogCleaner"):
        self.data_dir = data_dir
        self.cleaner = cleaner

    async def handle_status(self) -> str:
        """处理 status 命令"""
        stats = self.cleaner.get_stats()

        lines = [
            "📊 日志状态",
            f"├─ 文件总数: {stats['total_files']}",
            f"├─ 总大小: {stats['total_size_mb']} MB",
            f"├─ 已压缩: {stats['compressed_count']} 个",
        ]

        if stats["oldest_file"]:
            lines.append(
                f"├─ 最早日志: {stats['oldest_file'].strftime('%Y-%m-%d %H:%M')}"
            )
        if stats["newest_file"]:
            lines.append(
                f"├─ 最新日志: {stats['newest_file'].strftime('%Y-%m-%d %H:%M')}"
            )

        lines.append("└─ 目录统计:")
        for dir_name, dir_stat in stats["directories"].items():
            size_mb = round(dir_stat["size"] / 1024 / 1024, 2)
            lines.append(f"   ├─ {dir_name}: {dir_stat['count']} 个, {size_mb} MB")

        return "\n".join(lines)

    async def handle_search(self, keyword: str, limit: int = 50) -> str:
        """处理 search 命令"""
        if not keyword:
            return "❌ 请提供搜索关键词"

        results = []
        count = 0

        for log_file in self.data_dir.rglob("*.log"):
            if count >= limit:
                break
            try:
                with open(log_file, encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            rel_path = log_file.relative_to(self.data_dir)
                            results.append(
                                f"[{rel_path}:{line_num}] {line.strip()[:100]}"
                            )
                            count += 1
                            if count >= limit:
                                break
            except Exception:
                pass

        if not results:
            return f"🔍 未找到包含 '{keyword}' 的日志"

        header = f"🔍 搜索 '{keyword}' 结果 (共 {len(results)} 条):\n"
        return header + "\n".join(results[:20])  # 最多显示20条

    async def handle_clean(self) -> str:
        """处理 clean 命令"""
        result = await self.cleaner.cleanup()

        freed_mb = round(result["freed_bytes"] / 1024 / 1024, 2)
        return (
            f"🧹 清理完成\n"
            f"├─ 压缩文件: {result['compressed']} 个\n"
            f"├─ 删除文件: {result['deleted']} 个\n"
            f"└─ 释放空间: {freed_mb} MB"
        )

    async def handle_export(self, days: int = 7) -> str:
        """处理 export 命令，导出最近N天日志"""
        export_dir = self.data_dir / "exports"
        export_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = export_dir / f"logs_export_{timestamp}.zip"

        cutoff = datetime.now().timestamp() - (days * 86400)
        file_count = 0

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for log_file in self.data_dir.rglob("*"):
                if log_file.is_file() and "exports" not in str(log_file):
                    if log_file.suffix in [".log", ".gz"]:
                        try:
                            if log_file.stat().st_mtime >= cutoff:
                                arcname = log_file.relative_to(self.data_dir)
                                zf.write(log_file, arcname)
                                file_count += 1
                        except Exception:
                            pass

        size_mb = round(zip_path.stat().st_size / 1024 / 1024, 2)
        return (
            f"📦 导出完成\n"
            f"├─ 文件: {zip_path}\n"
            f"├─ 包含: {file_count} 个日志文件\n"
            f"└─ 大小: {size_mb} MB"
        )

    def handle_help(self) -> str:
        """处理 help 命令"""
        return (
            "📋 LogPlus 命令帮助\n"
            "├─ /logplus status          查看日志状态\n"
            "├─ /logplus search <词>     搜索日志关键词\n"
            "├─ /logplus clean           手动清理旧日志\n"
            "├─ /logplus export [天]     导出最近N天日志(默认7天)\n"
            "├─ /logplus send all        发送全部日志文件\n"
            "├─ /logplus send errors     发送错误日志文件\n"
            "├─ /logplus send plugin <名> 发送指定插件日志\n"
            "└─ /logplus help            显示此帮助"
        )

    async def handle_send(self, target: str = "") -> tuple[str, Path | None]:
        """处理 send 命令，返回(消息文本, zip文件路径)"""
        if not target:
            return "❌ 请指定发送目标: all / errors / plugin <插件名>", None

        export_dir = self.data_dir / "exports"
        export_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if target == "all":
            return await self._pack_all_logs(export_dir, timestamp)
        elif target == "errors":
            return await self._pack_error_logs(export_dir, timestamp)
        else:
            # 尝试作为插件名处理
            return await self._pack_plugin_logs(export_dir, timestamp, target)

    async def _pack_all_logs(
        self, export_dir: Path, timestamp: str
    ) -> tuple[str, Path | None]:
        """打包全部日志"""
        zip_path = export_dir / f"all_logs_{timestamp}.zip"
        file_count = 0

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for log_file in self.data_dir.rglob("*"):
                if (
                    log_file.is_file()
                    and "exports" not in str(log_file)
                    and log_file.suffix in [".log", ".gz"]
                ):
                    try:
                        arcname = log_file.relative_to(self.data_dir)
                        zf.write(log_file, arcname)
                        file_count += 1
                    except Exception:
                        pass

        if file_count == 0:
            os.remove(zip_path)
            return "❌ 没有找到日志文件", None

        size_mb = round(zip_path.stat().st_size / 1024 / 1024, 2)
        message = f"📦 全部日志已打包\n├─ 文件数: {file_count}\n└─ 大小: {size_mb} MB"
        return message, zip_path

    async def _pack_error_logs(
        self, export_dir: Path, timestamp: str
    ) -> tuple[str, Path | None]:
        """打包错误日志"""
        zip_path = export_dir / f"error_logs_{timestamp}.zip"
        file_count = 0
        error_dir = self.data_dir / "errors"

        if not error_dir.exists():
            return "❌ 错误日志目录不存在", None

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for log_file in error_dir.rglob("*"):
                if log_file.is_file() and log_file.suffix in [".log", ".gz"]:
                    try:
                        arcname = log_file.relative_to(self.data_dir)
                        zf.write(log_file, arcname)
                        file_count += 1
                    except Exception:
                        pass

        if file_count == 0:
            os.remove(zip_path)
            return "❌ 没有找到错误日志文件", None

        size_mb = round(zip_path.stat().st_size / 1024 / 1024, 2)
        message = f"📦 错误日志已打包\n├─ 文件数: {file_count}\n└─ 大小: {size_mb} MB"
        return message, zip_path

    async def _pack_plugin_logs(
        self, export_dir: Path, timestamp: str, plugin_keyword: str
    ) -> tuple[str, Path | None]:
        """打包指定插件日志（支持关键词匹配）"""
        plugins_dir = self.data_dir / "plugins"

        if not plugins_dir.exists():
            return "❌ 插件日志目录不存在", None

        # 查找匹配的插件
        available_plugins = [d.name for d in plugins_dir.iterdir() if d.is_dir()]
        matched_plugins = [
            p for p in available_plugins if plugin_keyword.lower() in p.lower()
        ]

        if not matched_plugins:
            plugins_list = "\n".join(f"  - {p}" for p in available_plugins)
            return (
                f"❌ 未找到匹配 '{plugin_keyword}' 的插件\n可用插件:\n{plugins_list}",
                None,
            )

        if len(matched_plugins) > 1:
            plugins_list = "\n".join(f"  - {p}" for p in matched_plugins)
            return (
                f"❌ 找到多个匹配的插件，请更具体:\n{plugins_list}",
                None,
            )

        # 打包唯一匹配的插件日志
        plugin_name = matched_plugins[0]
        plugin_dir = plugins_dir / plugin_name
        zip_path = export_dir / f"plugin_{plugin_name}_{timestamp}.zip"
        file_count = 0

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for log_file in plugin_dir.rglob("*"):
                if log_file.is_file() and log_file.suffix in [".log", ".gz"]:
                    try:
                        arcname = log_file.relative_to(self.data_dir)
                        zf.write(log_file, arcname)
                        file_count += 1
                    except Exception:
                        pass

        if file_count == 0:
            os.remove(zip_path)
            return f"❌ 插件 '{plugin_name}' 没有日志文件", None

        size_mb = round(zip_path.stat().st_size / 1024 / 1024, 2)
        message = (
            f"📦 插件日志已打包\n"
            f"├─ 插件: {plugin_name}\n"
            f"├─ 文件数: {file_count}\n"
            f"└─ 大小: {size_mb} MB"
        )
        return message, zip_path
