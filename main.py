"""Main entry point for the bot."""
import asyncio
import logging
from aiogram import Bot, Dispatcher

from src.bot import (
    setup_logging,
    create_bot,
    create_dispatcher,
    on_startup,
    on_shutdown
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot."""
    # Setup logging
    setup_logging()
    
    # Create bot and dispatcher
    bot = create_bot()
    dp = create_dispatcher()
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # Start bot
        # ВАЖНО: явно указываем channel_post для получения обновлений из каналов
        await dp.start_polling(
            bot,
            allowed_updates=["message", "channel_post", "edited_channel_post"]
        )
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
