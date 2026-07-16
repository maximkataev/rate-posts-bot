"""Bot initialization and setup."""
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import settings
from src.handlers import admin, channel
from src.services.llm_service import llm_service

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_bot() -> Bot:
    """Create and configure bot instance."""
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )


def create_dispatcher() -> Dispatcher:
    """Create and configure dispatcher."""
    dp = Dispatcher()
    
    # Register routers
    dp.include_router(admin.router)
    dp.include_router(channel.router)
    
    return dp


async def on_startup(bot: Bot):
    """Actions on bot startup."""
    logger.info("Bot starting up...")

    # Get bot info
    bot_info = await bot.get_me()
    logger.info(f"Bot @{bot_info.username} started successfully")
    logger.info(f"Monitoring channel {settings.telegram_channel_id}")


async def on_shutdown(bot: Bot):
    """Actions on bot shutdown."""
    logger.info("Bot shutting down...")

    # Close LLM service
    await llm_service.close()

    logger.info("Bot stopped")
