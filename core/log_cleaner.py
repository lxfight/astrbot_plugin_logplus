import asyncio
import gzip
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class LogFileInfo:
    """日志文件信息"""

    path: Path
    size: int
    mtime: datetime
    is_compressed: bool


class LogCleaner:
    """日志清理器，负责压缩和清理旧日志"""

    def __init__(self, data_dir: Path, config: dict):
        self.data_dir = data_dir
        self.config = config
        self._task: asyncio.Task = None

    async def start(self):
        """启动定时清理任务"""
        if self._task is None:
            self._task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """停止清理任务"""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _cleanup_loop(self):
        """定时清理循环"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时检查一次
                await self.cleanup()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def cleanup(self) -> dict:
        """执行清理操作"""
        result = {"compressed": 0, "deleted": 0, "freed_bytes": 0}

        # 压缩旧日志
        if self.config.get("enable_compression", True):
            days = self.config.get("compression_after_days", 1)
            compressed = await self._compress_old_logs(days)
            result["compressed"] = compressed

        # 清理过期日志
        if self.config.get("auto_clean_enabled", True):
            max_age = self.config.get("max_age_days", 30)
            max_size = self.config.get("max_total_size_mb", 500) * 1024 * 1024
            deleted, freed = await self._clean_old_logs(max_age, max_size)
            result["deleted"] = deleted
            result["freed_bytes"] = freed

        return result

    async def _compress_old_logs(self, days: int) -> int:
        """压缩超过指定天数的日志"""
        count = 0
        threshold = datetime.now() - timedelta(days=days)

        for log_file in self._scan_log_files():
            if log_file.is_compressed:
                continue
            if log_file.mtime < threshold:
                if await self._compress_file(log_file.path):
                    count += 1

        return count

    async def _compress_file(self, filepath: Path) -> bool:
        """异步压缩文件"""
        try:
            gz_path = filepath.with_suffix(filepath.suffix + ".gz")
            await asyncio.to_thread(self._do_compress, filepath, gz_path)
            return True
        except Exception:
            return False

    def _do_compress(self, src: Path, dst: Path):
        """同步压缩操作"""
        with open(src, "rb") as f_in:
            with gzip.open(dst, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(src)

    async def _clean_old_logs(
        self, max_age_days: int, max_total_size: int
    ) -> tuple[int, int]:
        """清理过期和超量日志"""
        deleted = 0
        freed = 0
        threshold = datetime.now() - timedelta(days=max_age_days)

        # 获取所有日志文件并按时间排序
        files = sorted(self._scan_log_files(), key=lambda x: x.mtime)
        total_size = sum(f.size for f in files)

        for log_file in files:
            should_delete = False

            # 检查是否过期
            if log_file.mtime < threshold:
                should_delete = True

            # 检查总大小是否超限
            if total_size > max_total_size:
                should_delete = True

            if should_delete:
                try:
                    size = log_file.size
                    os.remove(log_file.path)
                    deleted += 1
                    freed += size
                    total_size -= size
                except Exception:
                    pass

        return deleted, freed

    def _scan_log_files(self) -> list[LogFileInfo]:
        """扫描所有日志文件"""
        files = []
        for path in self.data_dir.rglob("*"):
            if path.is_file() and (path.suffix == ".log" or ".log." in path.name):
                try:
                    stat = path.stat()
                    files.append(
                        LogFileInfo(
                            path=path,
                            size=stat.st_size,
                            mtime=datetime.fromtimestamp(stat.st_mtime),
                            is_compressed=path.suffix == ".gz",
                        )
                    )
                except Exception:
                    pass
        return files

    def get_stats(self) -> dict:
        """获取日志统计信息"""
        files = self._scan_log_files()
        total_size = sum(f.size for f in files)
        compressed_count = sum(1 for f in files if f.is_compressed)

        # 按目录统计
        dir_stats = {}
        for f in files:
            rel_path = f.path.relative_to(self.data_dir)
            top_dir = rel_path.parts[0] if rel_path.parts else "root"
            if top_dir not in dir_stats:
                dir_stats[top_dir] = {"count": 0, "size": 0}
            dir_stats[top_dir]["count"] += 1
            dir_stats[top_dir]["size"] += f.size

        return {
            "total_files": len(files),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "compressed_count": compressed_count,
            "directories": dir_stats,
            "oldest_file": min((f.mtime for f in files), default=None),
            "newest_file": max((f.mtime for f in files), default=None),
        }
