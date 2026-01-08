from typing import Any


class ConfigManager:
    """配置管理器"""

    DEFAULTS = {
        "log_level": "DEBUG",
        "max_file_size_mb": 10,
        "backup_count": 5,
        "rotation_strategy": "size",
        "rotation_interval": "daily",
        "enable_all_log": True,
        "enable_core_log": True,
        "enable_error_log": True,
        "enable_plugin_separation": True,
        "enable_compression": True,
        "compression_after_days": 1,
        "auto_clean_enabled": True,
        "max_total_size_mb": 500,
        "max_age_days": 30,
        "enable_sensitive_filter": True,
        "sensitive_keywords": "token,password,secret,api_key,apikey,access_key,accesskey",
    }

    def __init__(self, config: dict):
        self._config = config or {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持默认值"""
        if key in self._config:
            return self._config[key]
        if key in self.DEFAULTS:
            return self.DEFAULTS[key]
        return default

    def get_sensitive_keywords(self) -> list[str]:
        """获取敏感词列表"""
        keywords_str = self.get("sensitive_keywords", "")
        if isinstance(keywords_str, str):
            return [k.strip() for k in keywords_str.split(",") if k.strip()]
        return keywords_str if isinstance(keywords_str, list) else []

    def as_dict(self) -> dict:
        """返回完整配置字典"""
        result = dict(self.DEFAULTS)
        result.update(self._config)
        return result

    def update(self, config: dict):
        """更新配置"""
        self._config.update(config)
