import os
from pathlib import Path


class LogRouter:
    """日志路由器，负责日志来源判断和路径解析"""

    PLUGIN_PATHS = ["data/plugins", "astrbot/builtin_stars/"]

    @staticmethod
    def is_plugin_path(pathname: str) -> bool:
        """判断路径是否来自插件"""
        norm_path = os.path.normpath(pathname)
        return any(p in norm_path for p in LogRouter.PLUGIN_PATHS)

    @staticmethod
    def extract_plugin_name(pathname: str) -> str | None:
        """从路径提取插件名"""
        norm_path = os.path.normpath(pathname)
        parts = norm_path.split(os.sep)

        # data/plugins/plugin_name/...
        if "plugins" in parts:
            try:
                idx = parts.index("plugins")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
            except ValueError:
                pass

        # astrbot/builtin_stars/plugin_name/...
        if "builtin_stars" in parts:
            try:
                idx = parts.index("builtin_stars")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
            except ValueError:
                pass

        return None

    @staticmethod
    def get_source_type(pathname: str) -> str:
        """获取日志来源类型: plugin 或 core"""
        return "plugin" if LogRouter.is_plugin_path(pathname) else "core"

    @staticmethod
    def get_log_dir(data_dir: Path, pathname: str) -> Path:
        """根据日志来源获取日志目录"""
        if LogRouter.is_plugin_path(pathname):
            plugin_name = LogRouter.extract_plugin_name(pathname)
            if plugin_name:
                return data_dir / "plugins" / plugin_name
            return data_dir / "plugins" / "unknown"
        return data_dir / "core"
