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
            "├─ /logplus status       查看日志状态\n"
            "├─ /logplus search <词>  搜索日志关键词\n"
            "├─ /logplus clean        手动清理旧日志\n"
            "├─ /logplus export [天]  导出最近N天日志(默认7天)\n"
            "└─ /logplus help         显示此帮助"
        )
