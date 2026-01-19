import gzip
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

_compress_executor = ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="logplus_compress"
)


class CompressedRotatingFileHandler(RotatingFileHandler):
    """支持压缩的大小轮换Handler"""

    def __init__(
        self,
        filename,
        mode="a",
        maxBytes=0,
        backupCount=0,
        encoding=None,
        delay=False,
        enable_compression=True,
    ):
        self.enable_compression = enable_compression
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            # 异步压缩最旧的文件
            if self.enable_compression:
                oldest = f"{self.baseFilename}.{self.backupCount}"
                if os.path.exists(oldest):
                    _compress_executor.submit(_compress_file_sync, oldest)

            # 轮换文件
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)

            dfn = self.rotation_filename(f"{self.baseFilename}.1")
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)

        if not self.delay:
            self.stream = self._open()


def _compress_file_sync(filepath: str):
    """在线程池中同步压缩文件"""
    gz_path = f"{filepath}.gz"
    try:
        with open(filepath, "rb") as f_in:
            with gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(filepath)
    except Exception:
        pass


class CompressedTimedRotatingFileHandler(TimedRotatingFileHandler):
    """支持压缩的时间轮换Handler"""

    def __init__(
        self,
        filename,
        when="D",
        interval=1,
        backupCount=0,
        encoding=None,
        delay=False,
        utc=False,
        atTime=None,
        enable_compression=True,
    ):
        self.enable_compression = enable_compression
        super().__init__(
            filename, when, interval, backupCount, encoding, delay, utc, atTime
        )

    def doRollover(self):
        super().doRollover()
        if self.enable_compression and self.backupCount > 0:
            _compress_executor.submit(
                _compress_old_files_sync,
                os.path.dirname(self.baseFilename),
                os.path.basename(self.baseFilename),
                self.baseFilename,
            )


def _compress_old_files_sync(dir_path: str, base_name: str, current_file: str):
    """在线程池中同步压缩旧日志文件"""
    now = datetime.now()
    try:
        for filename in os.listdir(dir_path):
            if filename.startswith(base_name) and not filename.endswith(".gz"):
                filepath = os.path.join(dir_path, filename)
                if filepath == current_file:
                    continue
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if (now - mtime).days >= 1:
                        _compress_file_sync(filepath)
                except Exception:
                    pass
    except Exception:
        pass


class LogPlusHandler(logging.Handler):
    """日志增强主Handler，负责分发日志到各个文件"""

    def __init__(self, data_dir: Path, config: dict, sensitive_filter=None):
        super().__init__()
        self.data_dir = data_dir
        self.config = config
        self.sensitive_filter = sensitive_filter
        self.handlers: dict[str, logging.Handler] = {}
        self._init_directories()
        self._init_handlers()

    def _init_directories(self):
        """初始化日志目录"""
        dirs = ["all", "core", "errors", "plugins"]
        for d in dirs:
            (self.data_dir / d).mkdir(parents=True, exist_ok=True)

    def _init_handlers(self):
        """初始化各类日志Handler"""
        max_bytes = self.config.get("max_file_size_mb", 10) * 1024 * 1024
        backup_count = self.config.get("backup_count", 5)
        strategy = self.config.get("rotation_strategy", "size")
        interval = self.config.get("rotation_interval", "daily")
        enable_compression = self.config.get("enable_compression", True)

        # 全局日志
        if self.config.get("enable_all_log", True):
            self.handlers["all"] = self._create_handler(
                self.data_dir / "all" / "all.log",
                max_bytes,
                backup_count,
                strategy,
                interval,
                enable_compression,
            )

        # Core日志
        if self.config.get("enable_core_log", True):
            self.handlers["core"] = self._create_handler(
                self.data_dir / "core" / "core.log",
                max_bytes,
                backup_count,
                strategy,
                interval,
                enable_compression,
            )

        # 错误日志
        if self.config.get("enable_error_log", True):
            handler = self._create_handler(
                self.data_dir / "errors" / "error.log",
                max_bytes,
                backup_count,
                strategy,
                interval,
                enable_compression,
            )
            handler.setLevel(logging.ERROR)
            self.handlers["error"] = handler

    def _create_handler(
        self,
        filepath: Path,
        max_bytes: int,
        backup_count: int,
        strategy: str,
        interval: str,
        enable_compression: bool,
    ) -> logging.Handler:
        """根据策略创建对应的Handler"""
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if strategy == "time":
            when = "H" if interval == "hourly" else "D"
            handler = CompressedTimedRotatingFileHandler(
                str(filepath),
                when=when,
                backupCount=backup_count,
                encoding="utf-8",
                enable_compression=enable_compression,
            )
        else:  # size 或 hybrid
            handler = CompressedRotatingFileHandler(
                str(filepath),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
                enable_compression=enable_compression,
            )

        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)-5s] [%(filename)s:%(lineno)d]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        return handler

    def get_plugin_handler(self, plugin_name: str) -> logging.Handler:
        """获取或创建插件专属Handler"""
        key = f"plugin_{plugin_name}"
        if key not in self.handlers:
            plugin_dir = self.data_dir / "plugins" / plugin_name
            max_bytes = self.config.get("max_file_size_mb", 10) * 1024 * 1024
            backup_count = self.config.get("backup_count", 5)
            strategy = self.config.get("rotation_strategy", "size")
            interval = self.config.get("rotation_interval", "daily")
            enable_compression = self.config.get("enable_compression", True)

            self.handlers[key] = self._create_handler(
                plugin_dir / "plugin.log",
                max_bytes,
                backup_count,
                strategy,
                interval,
                enable_compression,
            )
        return self.handlers[key]

    def emit(self, record: logging.LogRecord):
        """处理日志记录"""
        try:
            # 复制 record 并进行脱敏，避免影响其他 Handler
            if self.sensitive_filter:
                record = self.sensitive_filter.mask_record(record)

            # 写入全局日志
            if "all" in self.handlers:
                self.handlers["all"].emit(record)

            # 判断来源并写入对应日志
            is_plugin = self._is_plugin_path(record.pathname)

            if is_plugin:
                plugin_name = self._extract_plugin_name(record.pathname)
                if plugin_name and self.config.get("enable_plugin_separation", True):
                    handler = self.get_plugin_handler(plugin_name)
                    handler.emit(record)
            else:
                # Core日志
                if "core" in self.handlers:
                    self.handlers["core"].emit(record)

            # 错误日志
            if "error" in self.handlers and record.levelno >= logging.ERROR:
                self.handlers["error"].emit(record)

            # 确保及时写入磁盘
            self._flush_handlers()

        except Exception:
            self.handleError(record)

    def _flush_handlers(self):
        """刷新所有handler缓冲区以确保及时写入"""
        for handler in self.handlers.values():
            try:
                handler.flush()
            except Exception:
                pass

    def _is_plugin_path(self, pathname: str) -> bool:
        """判断是否来自插件目录"""
        norm_path = os.path.normpath(pathname)
        return "data/plugins" in norm_path or "astrbot/builtin_stars/" in norm_path

    def _extract_plugin_name(self, pathname: str) -> str | None:
        """从路径提取插件名"""
        norm_path = os.path.normpath(pathname)

        # data/plugins/plugin_name/...
        if "data/plugins" in norm_path:
            parts = norm_path.split(os.sep)
            try:
                idx = parts.index("plugins")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
            except ValueError:
                pass

        # astrbot/builtin_stars/plugin_name/...
        if "builtin_stars" in norm_path:
            parts = norm_path.split(os.sep)
            try:
                idx = parts.index("builtin_stars")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
            except ValueError:
                pass

        return None

    def close(self):
        """关闭所有Handler"""
        for handler in self.handlers.values():
            handler.close()
        self.handlers.clear()
        super().close()
