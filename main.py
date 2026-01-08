import asyncio
import logging
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, StarTools, register

from .core.command_handler import CommandHandler
from .core.config_manager import ConfigManager
from .core.log_cleaner import LogCleaner
from .core.log_handler import LogPlusHandler
from .core.sensitive_filter import SensitiveFilter


@register(
    "LogPlus",
    "lxfight",
    "AstrBot日志增强插件，支持日志持久化、按插件分类、轮换、压缩、自动清理等功能",
    "1.0.0",
    "https://github.com/lxfight/astrbot_plugin_logplus",
)
class LogPlusPlugin(Star):
    """LogPlus 日志增强插件"""

    def __init__(self, context: Context, config: dict[str, Any]):
        super().__init__(context)
        self.context = context

        data_dir = str(StarTools.get_data_dir())

        self.config_manager = ConfigManager(config)
        self.log_handler: LogPlusHandler | None = None
        self.log_cleaner: LogCleaner | None = None
        self.sensitive_filter: SensitiveFilter | None = None
        self.command_handler: CommandHandler | None = None

        asyncio.create_task(self._initialize_plugin(data_dir))

    async def _initialize_plugin(self, data_dir: str):
        """异步初始化插件"""
        try:
            config = self.config_manager.as_dict()

            if config.get("enable_sensitive_filter", True):
                keywords = self.config_manager.get_sensitive_keywords()
                self.sensitive_filter = SensitiveFilter(keywords=keywords, enabled=True)

            self.log_handler = LogPlusHandler(data_dir, config)

            level_name = config.get("log_level", "DEBUG")
            level = getattr(logging, level_name.upper(), logging.DEBUG)
            self.log_handler.setLevel(level)

            if self.sensitive_filter:
                self.log_handler.addFilter(self.sensitive_filter)

            astrbot_logger = logging.getLogger("astrbot")
            astrbot_logger.addHandler(self.log_handler)

            self.log_cleaner = LogCleaner(data_dir, config)
            await self.log_cleaner.start()

            self.command_handler = CommandHandler(data_dir, self.log_cleaner)

            logger.info(f"✅ LogPlus 插件已启动，日志目录: {data_dir}")

        except Exception as e:
            logger.error(f"LogPlus 插件初始化失败: {e}", exc_info=True)

    async def terminate(self):
        """插件停止时清理"""
        if self.log_cleaner:
            await self.log_cleaner.stop()

        if self.log_handler:
            astrbot_logger = logging.getLogger("astrbot")
            astrbot_logger.removeHandler(self.log_handler)
            self.log_handler.close()

        logger.info("LogPlus 插件已停止")

    @filter.command_group("logplus")
    def logplus(self):
        """LogPlus 命令组"""
        pass

    @logplus.command("status")
    async def cmd_status(self, event: AstrMessageEvent):
        """查看日志状态"""
        if not self.command_handler:
            yield event.plain_result("❌ 插件尚未初始化完成")
            return
        result = await self.command_handler.handle_status()
        yield event.plain_result(result)

    @logplus.command("search")
    async def cmd_search(self, event: AstrMessageEvent, keyword: str = ""):
        """搜索日志"""
        if not self.command_handler:
            yield event.plain_result("❌ 插件尚未初始化完成")
            return
        result = await self.command_handler.handle_search(keyword)
        yield event.plain_result(result)

    @logplus.command("clean")
    async def cmd_clean(self, event: AstrMessageEvent):
        """手动清理日志"""
        if not self.command_handler:
            yield event.plain_result("❌ 插件尚未初始化完成")
            return
        result = await self.command_handler.handle_clean()
        yield event.plain_result(result)

    @logplus.command("export")
    async def cmd_export(self, event: AstrMessageEvent, days: int = 7):
        """导出日志"""
        if not self.command_handler:
            yield event.plain_result("❌ 插件尚未初始化完成")
            return
        result = await self.command_handler.handle_export(days)
        yield event.plain_result(result)

    @logplus.command("help")
    async def cmd_help(self, event: AstrMessageEvent):
        """显示帮助"""
        if not self.command_handler:
            yield event.plain_result("❌ 插件尚未初始化完成")
            return
        result = self.command_handler.handle_help()
        yield event.plain_result(result)
