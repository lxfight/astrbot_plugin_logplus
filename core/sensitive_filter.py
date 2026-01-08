import logging
import re


class SensitiveFilter(logging.Filter):
    """敏感信息脱敏过滤器"""

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
        super().__init__()
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

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤并脱敏敏感信息"""
        if not self.enabled:
            return True

        if hasattr(record, "msg") and record.msg:
            record.msg = self._mask_sensitive(str(record.msg))

        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._mask_sensitive(str(v)) for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_sensitive(str(arg)) for arg in record.args
                )

        return True

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
