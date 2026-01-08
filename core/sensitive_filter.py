import copy
import logging
import re


class SensitiveFilter:
    """敏感信息脱敏处理器

    注意: 此类不再继承 logging.Filter，而是作为独立的脱敏工具。
    应在 Handler.emit 中对复制的 LogRecord 调用 mask_record 方法，
    以避免影响其他 Handler。

    仅支持 f-string 格式日志中 key=value 模式的脱敏。
    对于参数化日志 (logger.info("%s", value))，会对 args 中的值进行独立检测。
    """

    DEFAULT_KEYWORDS = [
        "token",
        "password",
        "passwd",
        "pwd",
        "secret",
        "api_key",
        "apikey",
        "access_key",
        "accesskey",
        "private_key",
        "privatekey",
        "credential",
        "auth",
    ]

    MASK = "***"

    def __init__(self, keywords: list[str] = None, enabled: bool = True):
        self.enabled = enabled
        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.patterns = []

        for keyword in self.keywords:
            # 匹配 key=value 或 key: value 或 "key": "value"
            patterns = [
                # key=value
                rf'({keyword})\s*=\s*["\']?([^"\'\s,}}\]]+)["\']?',
                # key: value
                rf'({keyword})\s*:\s*["\']?([^"\'\s,}}\]]+)["\']?',
                # "key": "value"
                rf'["\']({keyword})["\']\s*:\s*["\']([^"\']+)["\']',
            ]
            for p in patterns:
                self.patterns.append(re.compile(p, re.IGNORECASE))

    def mask_record(self, record: logging.LogRecord) -> logging.LogRecord:
        """对 LogRecord 进行脱敏处理，返回副本以避免影响其他 Handler"""
        if not self.enabled:
            return record

        masked_record = copy.copy(record)

        if hasattr(masked_record, "msg") and masked_record.msg:
            masked_record.msg = self._mask_sensitive(str(masked_record.msg))

        if hasattr(masked_record, "args") and masked_record.args:
            if isinstance(masked_record.args, dict):
                masked_record.args = {
                    k: self._mask_sensitive(str(v))
                    for k, v in masked_record.args.items()
                }
            elif isinstance(masked_record.args, tuple):
                masked_record.args = tuple(
                    self._mask_sensitive(str(arg)) for arg in masked_record.args
                )

        return masked_record

    def _mask_sensitive(self, text: str) -> str:
        """脱敏敏感信息"""
        result = text
        for pattern in self.patterns:
            result = pattern.sub(rf"\1={self.MASK}", result)
        return result

    def update_keywords(self, keywords: list[str]):
        """更新敏感词列表"""
        self.keywords = keywords
        self._compile_patterns()
